# -*- coding: utf-8 -*-

from openerp import models, fields, api


class Users(models.Model):
    _inherit = 'res.users'

    manager_id = fields.Many2one('res.users', string=u'Руководитель')
