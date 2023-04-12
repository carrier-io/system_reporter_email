#!/usr/bin/python3
# coding=utf-8

#   Copyright 2022 getcarrier.io
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

""" Slot """
import json
from random import random
from typing import Optional

from pylon.core.tools import log  # pylint: disable=E0611,E0401
from pylon.core.tools import web  # pylint: disable=E0611,E0401
from tools import task_tools, data_tools, constants
from time import sleep

from pydantic import BaseModel
from ..models.integration_pd import TaskSettingsModel


class Event:  # pylint: disable=E1101,R0903
    """
        Event Resource
    """
    integration_name = "system_reporter_email"

    @staticmethod
    def _tmp_fail_odd(num: int):
        if num % 2 != 0:
            sleep(5)
            raise Exception('Custom message here. Host cannot be odd')

    @staticmethod
    def _prepare_task(integration_data: dict) -> dict:
        env_vars = TaskSettingsModel.parse_obj({
            **integration_data['settings'],
            'project_id': integration_data["project_id"]
        })
        return {
            'funcname': f'email_integration_{integration_data["id"]}',
            'invoke_func': 'lambda_function.lambda_handler',
            'runtime': 'Python 3.7',
            'env_vars': env_vars.json(),
            'region': 'default'
        }

    @web.event(f"{integration_name}_created_or_updated")
    def _created_or_updated(self, context, event, payload):
        project = context.rpc_manager.call.project_get_or_404(project_id=payload["project_id"])
        log.info('reporter email %s', payload['settings'])
        if not payload['task_id']:
            context.rpc_manager.call.integrations_update_attrs(
                integration_id=payload['id'],
                update_dict={'status': 'pending'},
                return_result=False
            )
            try:
                #Event._tmp_fail_odd(payload['settings']['port'])  # todo: remove
                email_task = task_tools.create_task(
                    project,
                    data_tools.files.File(constants.EMAIL_INVITATION_PATH),
                    Event._prepare_task(payload),
                )
                log.info('reporter task id %s', email_task.task_id)
                # updated_data = self.context.rpc_manager.call.integrations_set_task_id(
                #     integration_data['id'],
                #     email_task.task_id,
                #     'success'
                # )
                updated_data = context.rpc_manager.call.integrations_update_attrs(
                    integration_id=payload['id'],
                    update_dict={'status': 'success', 'task_id': email_task.task_id},
                    return_result=True
                )
                # self.context.rpc_manager.call.integrations_update_attrs(payload['id'], {'status': 'pending'})

                context.sio.emit('task_creation', {
                    'ok': True,
                    **updated_data
                })
            except Exception as e:
                # updated_data = self.context.rpc_manager.call.integrations_set_task_id(payload['id'], None, 'error')
                updated_data = context.rpc_manager.call.integrations_update_attrs(
                    integration_id=payload['id'],
                    update_dict={'status': str(e)},
                    return_result=True
                )
                log.error('Couldn\'t create task. %s', e)
                context.sio.emit("task_creation", {
                    'ok': False,
                    'msg': f'Couldn\'t create task for {updated_data["name"]} with id: {updated_data["id"]}. {e}',
                    **updated_data
                })
        else:  # task already created
            updated_env_vars = Event._prepare_task(payload)['env_vars']
            context.rpc_manager.call.tasks_update_env(
                project_id=project.id,
                task_id=payload['task_id'],
                env_vars=updated_env_vars,
                rewrite=True
            )
            context.sio.emit('task_creation', {
                'ok': True,
                'msg': 'Email task updated'
            })
