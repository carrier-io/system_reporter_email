from pylon.core.tools import log, web
from tools import constants as c


class Slot:
    @web.slot('administration_email_invitation_content')
    def administration_email_invitation_content(self, context, slot, payload):
        log.info('SYSYSYYS %s', payload)
        integrations = context.rpc_manager.call.integrations_get_project_integrations_by_name(
            project_id=None,
            integration_name=self.descriptor.name,
            mode=c.ADMINISTRATION_MODE
        )
        with context.app.app_context():
            return self.descriptor.render_template(
                'administration/content.html',
                integrations=integrations,
                integrations_url='/~/administration/~/configuration/integrations'
            )

    @web.slot('users_email_invitation_content')
    def users_email_invitation_content(self, context, slot, payload):
        log.info('SYSYSYYS %s', payload)
        admin_integrations = context.rpc_manager.call.integrations_get_project_integrations_by_name(
            project_id=None,
            integration_name=self.descriptor.name,
            mode=c.ADMINISTRATION_MODE
        )
        project_integrations = context.rpc_manager.call.integrations_get_project_integrations_by_name(
            project_id=payload['project_id'],
            integration_name=self.descriptor.name,
            mode=c.DEFAULT_MODE
        )
        with context.app.app_context():
            return self.descriptor.render_template(
                'administration/content.html',
                integrations=[*project_integrations, *admin_integrations],
                integrations_url='/configuration/integrations'
            )

    # @web.slot(f'integrations_{section_name}_scripts')
    # def integration_create_modal_scripts(self, context, slot, payload):
    #     with context.app.app_context():
    #         return self.descriptor.render_template(
    #             'integration/scripts.html',
    #         )
