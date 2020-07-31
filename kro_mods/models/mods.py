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

    @api.onchange('date_end_ex')
    def onchange_date_end_ex(self):
        if self.date_end_ex and self._origin.date_end_ex and self.state != 'plan':
            self.history_record(u'Срок выполнения изменен\t%s->%s' % (self._origin.date_end_ex, self.date_end_ex))
            self.archive_notification('Execution')

    @api.onchange('date_end_pr')
    def onchange_date_end_pr(self):
        if self.date_end_pr and self._origin.date_end_pr and self.state != 'plan':
            self.history_record(u'Срок утверждения изменен\t%s->%s' % (self._origin.date_end_pr, self.date_end_pr))
            self.archive_notification('Stating')

    @api.onchange('date_end_ap')
    def onchange_date_end_ap(self):
        if self.date_end_ap and self._origin.date_end_ap and self.state != 'plan':
            self.history_record(u'Срок подтверждения изменен\t%s->%s' % (self._origin.date_end_ap, self.date_end_ap))
            self.archive_notification('Approvement')

    @api.onchange('user_predicator_id')
    def onchange_user_predicator_id(self):
        if self.user_predicator_id and self._origin.user_predicator_id and self.state != 'plan':
            self.history_record(u'Утверждающий изменен\t%s->%s' % (self._origin.user_predicator_id.name, self.user_predicator_id.name))
            self.archive_notification('Stating')

    @api.onchange('user_approver_id')
    def onchange_user_approver_id(self):
        if self.user_approver_id and self._origin.user_approver_id and self.state != 'plan':
            self.history_record(u'Подтверждающий изменен\t%s->%s' % (self._origin.user_approver_id.name, self.user_approver_id.name))
            self.archive_notification('Approvement')

    @api.multi
    def archive_notification(self, note):
        for r in self:
            new_hist = ''
            for l in r.notifications_history.splitlines():
                if note in l.split('\t')[1].split():
                    new_hist += '-\t' + l + '\n'
                else:
                    new_hist += l + '\n'
            r.notifications_history = new_hist
