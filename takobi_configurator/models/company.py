from odoo import models
from odoo.tools.safe_eval import safe_eval


class Company(models.Model):
    _inherit = 'res.company'

    def _download_company_configuration(self):
        installed_modules = modules_to_configure = self.env['ir.module.module'].search([
            ("state", "=", "installed")]).mapped("name")
        res = self.env['ir.module.module']._download_takobi_configurations(
            modules_to_configure, installed_modules)
        eval_context = {
            'self': self.sudo(),
        }
        for config in res['company_configurations']:
            safe_eval(config.strip(), eval_context, mode="exec", nocopy=True)
