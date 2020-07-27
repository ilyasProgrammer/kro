# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
import datetime


class TaskMod(models.Model):
    _inherit = 'project.task'

    mark_state = fields.Integer(string=u'Оценка статуса', track_visibility='onchange', group_operator='avg')
    mark_result = fields.Integer(string=u'Оценка результата', track_visibility='onchange', group_operator='avg')
    notifications_history = fields.Text(default='', copy=False)
    task_type = fields.Selection([('strat', 'Стратегическое'), ('tact', 'Тактическое')], string=u'Тип')

    @api.onchange('user_executor_id')
    def onchange_user_executor_id(self):
        self.notifications_history = ''
