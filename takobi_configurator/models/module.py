import requests
from odoo import models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class Module(models.Model):
    _inherit = 'ir.module.module'

    def _download_takobi_configurations(self, modules_to_configure, installed_modules):
        takobi_configurator_endpoint = self.env['ir.config_parameter'].get_param(
            "takobi.configurator.endpoint", "https://takobi.online/takobi/modules/configurations")
        contract_name = self.env['ir.config_parameter'].get_param("takobi.contract.name")
        contract_secret = self.env['ir.config_parameter'].get_param("takobi.contract.secret")
        if not contract_name:
            contract_name = self.env.cr.dbname
        data = {
            'contract_name': contract_name,
            'contract_secret':contract_secret,
            'modules_to_configure': ','.join(modules_to_configure),
            'installed_modules': ','.join(installed_modules),
        }
        r = requests.post(takobi_configurator_endpoint, data=data)
        if r.status_code != 200:
            raise UserError("Error while calling %s: [%s] %s" % (takobi_configurator_endpoint, r.status_code, r.reason))
        return r.json()

    def next(self):
        configured_modules = self.env['ir.config_parameter'].get_param("takobi.configured.modules")
        if configured_modules:
            configured_modules = configured_modules.split(",")
        else:
            configured_modules = []
        installed_modules = self.search([("state", "=", "installed")]).mapped("name")
        modules_to_configure = list(set(installed_modules) - set(configured_modules))
        res = self._download_takobi_configurations(modules_to_configure, installed_modules)
        eval_context = {
            'self': self.env.user.company_id.sudo(),
        }
        for config in res['generic_configurations']:
            safe_eval(config.strip(), eval_context, mode="exec", nocopy=True)
        companies = self.env['res.company'].sudo().search([])
        for company in companies:
            eval_context = {
                'self': company,
            }
            for config in res['company_configurations']:
                safe_eval(config.strip(), eval_context, mode="exec", nocopy=True)
        self.env['ir.config_parameter'].set_param(
            "takobi.configured.modules", ",".join(installed_modules))
        return super(Module, self).next()
