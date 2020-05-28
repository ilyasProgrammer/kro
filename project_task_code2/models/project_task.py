# -*- coding: utf-8 -*-
# Copyright 2016 Tecnativa <vicent.cubells@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _


class ProjectTask(models.Model):
    _inherit = 'project.task'
    _order = 'code'
    code = fields.Char(string=u'Номер', required=True, default="/")

    _sql_constraints = [
        ('project_task_unique_code', 'UNIQUE (code)',
         _('The code must be unique!')),
    ]

    @api.model
    def create(self, vals):
        if vals.get('code', '/') == '/':
            vals['code'] = self.env['ir.sequence'].next_by_code('project.task')
        return super(ProjectTask, self).create(vals)

    @api.one
    def copy(self, default=None):
        if default is None:
            default = {}
        default['code'] = self.env['ir.sequence'].next_by_code('project.task')
        return super(ProjectTask, self).copy(default)

