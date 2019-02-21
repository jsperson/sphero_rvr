#!/usr/bin/env python3

import asyncio
import logging
from .sphero_handler_base import SpheroHandlerBase
from ..protocol.api_sphero_protocol import ErrorCode
from ..protocol.api_sphero_message import Message


logger = logging.getLogger(__name__)


class Handler(SpheroHandlerBase):
    __slots__ = ['__sequences', '__command_workers', '__response_workers']

    def __init__(self, port, command_workers=None, response_workers=None):
        '''Knows how to handle Sphero API Commands in both directions

        Args:
            port (SpheroPortBase): A port instance that implements send(msg)

        Kwargs:
            command_workers (dict):
            response_workers (dict):

        '''
        SpheroHandlerBase.__init__(self, port)
        self.__sequences = list(range(1, 256))

        if command_workers is not None:
            self.__command_workers = command_workers
        else:
            self.__command_workers = {}

        if response_workers is not None:
            self.__response_workers = response_workers
        else:
            self.__response_workers = {}

    @property
    def command_workers(self):
        return self.__command_workers.copy()

    @property
    def response_workers(self):
        return self.__response_workers.copy()

    async def message_handler(self, msg):
        '''Handles API Messages (Commands and Responses)

        Pass to Parser
        '''
        if msg.is_response:
            await self._handle_response(msg)
            return

        err, response_body = await self._handle_command(msg)

        if not msg.requests_response:
            return

        if msg.requests_error_response and err is ErrorCode.SUCCESS:
            return

        response = Message.from_command_message(msg)
        response.err = err
        response.seq = msg.seq
        response.pack_bytes(response_body)
        self._port.send(response)

    async def error_handler(self, buf):
        '''Attempts to Handle Malformed API Messages

        Pass To Parser
        '''
        # TODO MJC Implement
        pass

    def add_command_worker(self, did, cid, target_node, handler):
        '''Add A Command Worker to this Handler's Dictionary

        Args:
            did (unsigned byte): Device ID
            cid (unsigned byte): Command ID
            target_node (unsigned byte): Target ID Node
            handler (func): Takes Message,
                            returns (ErrorCode, response_body) tuple

        Returns:
            None

        Raises:
            ValueError: A Worker for that DID/CID/TID already exists.
                        You must explicitly remove it before adding a new one.
        '''
        key = (did, cid, target_node)
        self._add_worker(
                self.__command_workers,
                key,
                handler
        )

    def remove_command_worker(self, did, cid, target_node):
        '''Remove A Command Worker from this Handler's Dictionary'''
        self._remove_worker(self.__command_workers, (did, cid, target_node))

    def add_response_worker(self, did, cid, seq, handler):
        '''Add A Response Worker to this Handler's Dictionary

        Args:
            did (unsigned byte): Device ID
            cid (unsigned byte): Command ID
            seq (unsigned byte): Sequence
            handler (func): Takes Message, returns unpacked Message Body

        Returns:
            None

        Raises:
            ValueError: A Worker for that DID/CID/SEQ already exists.
                        You must explicitly remove it before adding a new one.

        '''
        self._add_worker(self.__response_workers, (did, cid, seq), handler)

    def remove_response_worker(self, did, cid, seq):
        '''Remove A Response Worker from this Handler's Dictionary'''
        self._remove_worker(self.__response_workers, (did, cid, seq))

    async def send_command(self, msg, response_handler=None, timeout=None):
        '''Send a command to the port, returns the result (if requested)

        Args:
            msg (Message): an API Message

        Kwargs:
            response_handler (func): Unpacks response and returns the contents
            timeout (seconds): time to wait for a response

        Returns:
            The result of the response_handler, or None if a response_handler
            was not provided

        Raises:
            asyncio.TimeoutError: Response Timeout expired
            TypeError: - A response_handler was not provided for a msg that
                        requests a response, or
                       - A timeout was not provided for a msg that requests
                        an error response
            Exception: - A response with an ErrorCode other and SUCCESS was
                        received. arg[0] of the Excecption is the ErrorCode
                       - An exception occurred in the provided response_handler
        '''
        if msg.requests_response and response_handler is None:
            raise TypeError('Response Handler must be supplied for'
                            'messages that request responses')

        if msg.requests_error_response and timeout is None:
            raise TypeError('Timeout must be supplied for'
                            'messages that request error response')

        if response_handler is None:
            self._port.send(msg)
            return

        future = asyncio.Future()
        msg.seq = self.__sequences.pop()

        async def response_handler_wrapper(msg):
            try:
                if msg.err is not ErrorCode.SUCCESS:
                    raise Exception(msg.err.name)
                result = response_handler(msg)
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)
                pass

        self.add_response_worker(
                msg.did,
                msg.cid,
                msg.seq,
                response_handler_wrapper
        )

        self._port.send(msg)

        try:
            await asyncio.shield(asyncio.wait_for(future, timeout=timeout))
            return future.result()
        except Exception:
            raise
        finally:
            self.__sequences.append(msg.seq)
            self.remove_response_worker(msg.did, msg.cid, msg.seq)

    def _add_worker(self, worker_list, key, handler):
        if key in worker_list:
            raise ValueError
        worker_list[key] = handler

    def _remove_worker(self, worker_list, key):
        worker_list.pop(key)

    async def _handle_message(self, worker_list, msg, key):
        try:
            worker = worker_list[key]
            return await worker(msg)
        except KeyError:
            logger.warning('Response Handler Missing: {}'.format(key))
            pass
        except Exception as e:
            logger.error("Exception {} in {}".format(e, key))
            pass

    async def _handle_command(self, msg):
        key = (msg.did, msg.cid, msg.source_node)
        if key not in self.__command_workers:
            key = (msg.did, msg.cid, None)
        if key not in self.__command_workers:
            return ErrorCode.NOT_YET_IMPLEMENTED, b''

        return await self._handle_message(self.__command_workers, msg, key)

    async def _handle_response(self, msg):
        key = (msg.did, msg.cid, msg.seq)
        return await self._handle_message(self.__response_workers, msg, key)
