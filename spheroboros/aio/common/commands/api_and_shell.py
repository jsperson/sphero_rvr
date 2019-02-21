#!/usr/bin/env python3
# This file is automatically generated!
# Source File:        0x10-api_and_shell.json
# Device ID:          0x10
# Device Name:        api_and_shell
# Timestamp:          02/21/2019 @ 19:10:34.489757 (UTC)

from spheroboros.common.commands.api_and_shell import CommandsEnum
from spheroboros.common.devices import DevicesEnum
from spheroboros.common.parameter import Parameter


async def echo(self, data, target, timeout=None):
    return await self._dal.send_command(
        DevicesEnum.api_and_shell,
        CommandsEnum.echo,
        target,
        timeout,
        inputs=[
            Parameter(
                name='data',
                data_type='uint8_t',
                index=0,
                value=data,
                size=16
            ),
        ],
        outputs=[
            Parameter(
                name='data',
                data_type='uint8_t',
                index=0,
                size=16,
            ),
        ],
    )


async def get_api_protocol_version(self, target, timeout=None):
    return await self._dal.send_command(
        DevicesEnum.api_and_shell,
        CommandsEnum.get_api_protocol_version,
        target,
        timeout,
        outputs=[
            Parameter(
                name='majorVersion',
                data_type='uint8_t',
                index=0,
                size=1,
            ),
            Parameter(
                name='minorVersion',
                data_type='uint8_t',
                index=1,
                size=1,
            ),
        ],
    )


async def get_supported_dids(self, target, timeout=None):
    return await self._dal.send_command(
        DevicesEnum.api_and_shell,
        CommandsEnum.get_supported_dids,
        target,
        timeout,
        outputs=[
            Parameter(
                name='dids',
                data_type='uint8_t',
                index=0,
                size=9999,
            ),
        ],
    )


async def get_supported_cids(self, did, target, timeout=None):
    return await self._dal.send_command(
        DevicesEnum.api_and_shell,
        CommandsEnum.get_supported_cids,
        target,
        timeout,
        inputs=[
            Parameter(
                name='did',
                data_type='uint8_t',
                index=0,
                value=did,
                size=1
            ),
        ],
        outputs=[
            Parameter(
                name='cids',
                data_type='uint8_t',
                index=0,
                size=9999,
            ),
        ],
    )
