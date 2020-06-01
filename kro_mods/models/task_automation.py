# -*- coding: utf-8 -*-

from openerp import models, api, fields
import datetime
import logging

log = logging.getLogger(__name__)
DONE_STAGES = ['stating', 'stated', 'approvement', 'approved', 'finished']


class TaskMod(models.Model):
    _inherit = 'project.task'

    @api.model
    def cron_task_automation(self):
        # plan = self.env['project.task'].search([('state', '=', 'plan')])
        # plan = self.env['project.task'].search([('state', '=', 'plan'), ('user_id', 'in', [43, 98, 91, 66, 149])])
        plan = self.env['project.task'].search([('state', '=', 'plan'),
                                                ('user_id', 'in', [66]),
                                                ('date_start', '!=', False),
                                                ('date_end_ex', '!=', False),
                                                ])
        plan.process_plan_tasks()

    @api.multi
    def process_plan_tasks(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        now = datetime.datetime.now()
        kwargs = {'author_id': 1, 'subtype_id': 2}
        for rec in self:
            try:
                date = datetime.datetime.strptime(rec.create_date, '%Y-%m-%d %H:%M:%S')
                msg_text = ''
                date_diff = (now - date).days
                if date_diff > 31 and 'PLAN 1 note' not in rec.notifications_history:
                    msg_text = u"Прошу вывести задание из планирования или, если задание не актуально, то его завершить."
                    subject = u"Планирование > 31 дня"
                    rec.notifications_history += '%s\tPLAN 1 note\n' % str(now)
                elif date_diff > 34 and 'PLAN 2 note' not in rec.notifications_history:
                    subject = u"Планирование > 34 дней"
                    msg_text = u"При отсутствии ответа в течении 3х дней, с момента получения письма, задание автоматически перейдет в статус завершено."
                    rec.notifications_history += '%s\tPLAN 2 note\n' % str(now)
                elif date_diff > 40 and 'PLAN 3 note' not in rec.notifications_history:
                    subject = u"Планирование > 40 дней"
                    msg_text = u"Задание завершено."
                    rec.notifications_history += '%s\tPLAN 3 note\n' % str(now)
                    rec.state = 'finished'
                elif len(rec.depend_on_ids) > 0 and rec.all_prev_tasks_are_done():
                    if 'PLAN 1 depend on note' not in rec.notifications_history:
                        subject = u"Предыдущие задачи утверждаются"
                        msg_text = u"Прошу вывести задание."
                        rec.notifications_history += '%s\tPLAN 1 depend on note\n' % str(now)
                    elif 'PLAN 2 depend on note' not in rec.notifications_history:
                        if rec.get_note_period(now, 'PLAN 1 depend on note') > 3:
                            subject = u"Предыдущие задачи утверждаются"
                            msg_text = u"Прошу вывести задание 2й раз."
                            rec.notifications_history += '%s\tPLAN 2 depend on note\n' % str(now)
                    elif 'PLAN depend on 14 days note' not in rec.notifications_history:
                        if rec.get_note_period(now, 'PLAN 2 depend on note') > 14:
                            subject = u"14 Дней прошло"
                            msg_text = u"Задание неактуально, переведено в завершено."
                            rec.notifications_history += '%s\tPLAN depend on 14 days note\n' % str(now)
                if msg_text:
                    body = """<a href="%s/web#model=res.partner&amp;id=%s" """ % (base_url, rec.user_id.partner_id.id)
                    body += """class="cleaned_o_mail_redirect" data-oe-id="%s" """ % rec.user_id.partner_id.id
                    body += """data-oe-model="res.partner" target="_blank">@%s</a> """ % rec.user_id.partner_id.name
                    body += msg_text
                    kwargs['partner_ids'] = [rec.user_id.partner_id.id]
                    message = rec.message_post(body=body, subject=subject, message_type="email",  **kwargs)
                    log.info('Sent PLAN task message. %s %s', rec, message)
            except Exception as e:
                log.error(rec)
                log.error(e)

    @api.multi
    def all_prev_tasks_are_done(self):
        if len(self.depend_on_ids) > 0:
            if len(self.depend_on_ids.filtered(lambda x: x.state in DONE_STAGES)) == len(self.depend_on_ids):
                return True
            else:
                return False

    @api.multi
    def get_note_period(self, now, note):
        for l in self.notifications_history.splitlines():
            if l.split('\t')[1] == note:
                return (now - datetime.datetime.strptime(l.split('\t')[0], '%Y-%m-%d %H:%M:%S.%f')).days
        return 0
