# -*- coding: utf-8 -*-

from openerp import models, api, fields
from datetime import datetime
import logging
import time
import pytz
import numpy as np
import pytz

log = logging.getLogger(__name__)
DONE_STAGES = ['stating', 'stated', 'approvement', 'approved', 'finished']


class TaskMod(models.Model):
    _inherit = 'project.task'

    @api.model
    def cron_task_automation_plan(self):
        # plan = self.env['project.task'].search([('state', '=', 'plan'), ('user_id', 'in', [43, 98, 91, 66, 149])])
        log.info("Started cron")
        now = datetime.now(pytz.timezone(self.env.context.get('tz') or 'UTC'))
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        kwargs = {'author_id': 1, 'subtype_id': 2}
        plan = self.env['project.task'].search([('state', '=', 'plan'), ('date_start', '>', now), ('date_end_ex', '!=', False)])
        log.info("Plan tasks: %s", plan)
        plan.process_plan_tasks(base_url, kwargs)
        plan_soon_start = self.env['project.task'].search([('state', '=', 'plan'), ('date_start', '!=', False)])
        log.info("Plan tasks soon start: %s", plan_soon_start)
        plan_soon_start.process_plan_tasks_start_soon(base_url, kwargs)
        log.info("Finished cron")

    @api.multi
    def process_plan_tasks_start_soon(self, base_url, kwargs):
        now = datetime.now().date()
        for rec in self:
            try:
                date = datetime.strptime(rec.date_start, '%Y-%m-%d').date()
                date_diff = (now - date).days
                log.info("Date diff: %s %s", rec, str(date_diff))
                message = ''
                if 0 <= date_diff <= 3:
                    if 'PLAN START SOON 1 note' not in rec.notifications_history:
                        rec.notifications_history += '%s\tPLAN START SOON 1 note\n' % str(now)
                    elif 'PLAN START SOON 2 note' not in rec.notifications_history:
                        rec.notifications_history += '%s\tPLAN START SOON 2 note\n' % str(now)
                    elif 'PLAN START SOON 3 note' not in rec.notifications_history:
                        rec.notifications_history += '%s\tPLAN START SOON 3 note\n' % str(now)
                    elif 'PLAN START SOON 4 note' not in rec.notifications_history:
                        rec.notifications_history += '%s\tPLAN START SOON 4 note\n' % str(now)
                if message:
                    msg_text = u"Прошу вывести в согласование или перепланировать срок."
                    subject = u"Сегодня начало" if date_diff == 0 else u"Скоро начало"
                    body = """<a href="%s/web#model=res.partner&amp;id=%s" """ % (base_url, rec.user_id.partner_id.id)
                    body += """class="cleaned_o_mail_redirect" data-oe-id="%s" """ % rec.user_id.partner_id.id
                    body += """data-oe-model="res.partner" target="_blank">@%s</a> """ % rec.user_id.partner_id.name
                    body += msg_text
                    kwargs['partner_ids'] = [rec.user_id.partner_id.id]
                    message = rec.message_post(body=body, subject=subject, message_type="email",  **kwargs)
                    log.info('Sent PLAN task message starting soon. %s %s', rec, message)
                    time.sleep(1)
            except Exception as e:
                log.error(rec)
                log.error(e)

    @api.multi
    def process_plan_tasks(self, base_url, kwargs):
        now = datetime.now()
        for rec in self:
            try:
                date = datetime.strptime(rec.create_date, '%Y-%m-%d %H:%M:%S')
                msg_text = ''
                date_diff = (now - date).days
                log.info("Plan task date diff: %s %s", rec, str(date_diff))
                log.info("Note 1 period: %s %s", rec, str(rec.get_note_period(now, 'PLAN 1 note')))
                if date_diff > 31 and 'PLAN 1 note' not in rec.notifications_history:
                    msg_text = u"Прошу вывести задание из планирования или, если задание не актуально, то его завершить."
                    subject = u"Планирование > 31 дня"
                    rec.notifications_history += '%s\tPLAN 1 note\n' % str(now)
                elif rec.get_note_period(now, 'PLAN 1 note') > 2 and 'PLAN 2 note' not in rec.notifications_history:
                    subject = u"Планирование > 34 дней"
                    msg_text = u"При отсутствии ответа в течении 3х дней, с момента получения письма, задание автоматически перейдет в статус завершено."
                    rec.notifications_history += '%s\tPLAN 2 note\n' % str(now)
                elif rec.get_note_period(now, 'PLAN 2 note') > 2 and 'PLAN 3 note' not in rec.notifications_history:
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
                        if rec.get_note_period(now, 'PLAN 1 depend on note') > 2:
                            subject = u"Предыдущие задачи утверждаются"
                            msg_text = u"Прошу вывести задание 2й раз."
                            rec.notifications_history += '%s\tPLAN 2 depend on note\n' % str(now)
                    elif 'PLAN depend on 14 days note' not in rec.notifications_history:
                        if rec.get_note_period(now, 'PLAN 2 depend on note') > 13:
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
                    time.sleep(1)
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
                date = datetime.strptime(l.split('\t')[0], '%Y-%m-%d %H:%M:%S.%f')
                log.info("Rec %s Now %s date %s", self, now, date)
                return (now - date).days
        return 0

    @api.multi
    def get_state_date(self, state):
        for l in reversed(self.state_history.splitlines()):
            if l.split('\t')[1] == state:
                date = datetime.strptime(l.split('\t')[0], '%Y-%m-%d %H:%M:%S')
                return date
        return 0

    @api.multi
    def get_note_busday_period(self, now, note):
        for l in self.notifications_history.splitlines():
            if l.split('\t')[1] == note:
                date = datetime.strptime(l.split('\t')[0][:19], '%Y-%m-%d %H:%M:%S')
                return np.busday_count(date.date(), now.date())
        return 0

    @api.model
    def cron_task_automation_agreement(self):
        log.info("Started cron")
        agreement_tasks = self.env['project.task'].search([('state', '=', 'agreement'), ('date_start', '!=', False), ('date_end_ex', '!=', False)])
        log.info("Agreement tasks: %s", agreement_tasks)
        agreement_tasks.process_agreement_tasks()
        log.info("Finished cron")

    @api.multi
    def get_blocking_users(self, user_id):
        for b in self.blocking_user_ids.sorted(key=lambda r: r.id, reverse=True):  # Take last one
            if b.set_by_id == user_id:
                return b
        return False

    @api.multi
    def process_agreement_tasks(self):
        now = datetime.now(pytz.timezone('Asia/Yekaterinburg'))
        for rec in self:
            try:
                if 'Agreement 1 note' not in rec.notifications_history:
                    msg_text = u"Прошу согласовать в течение 24 часов."
                    subject = u"Согласование"
                    rec.notifications_history += '%s\tAgreement 1 note\n' % str(now)
                    if rec.user_approver_id and not rec.approved_by_approver:
                        rec.send_notification(rec.user_approver_id, msg_text, subject)
                    if rec.user_predicator_id and not rec.approved_by_predicator:
                        rec.send_notification(rec.user_predicator_id, msg_text, subject)
                    if rec.user_executor_id and not rec.approved_by_executor:
                        rec.send_notification(rec.user_executor_id, msg_text, subject)
                elif 'Agreement 1 note' in rec.notifications_history:
                    if rec.get_note_busday_period(now, 'Agreement 1 note') > 0:
                        msg_text = u"Задание не согласовывается, прошу сменить "
                        subject = u"Согласование просрочено"
                        if rec.user_executor_id and not rec.approved_by_executor:
                            executor_blockers = rec.get_blocking_users(rec.user_executor_id)
                            if executor_blockers:
                                period = (now.replace(tzinfo=None) - datetime.strptime(executor_blockers.create_date, '%Y-%m-%d %H:%M:%S')).days
                                if period > 0 and 'Agreement blocked note' not in rec.notifications_history:
                                    msg = "Вопрошаемый не отвечает. Спрашивал исполнитель: %s. Вопрос задан: %s" % (executor_blockers.set_by_id.name, executor_blockers.user_id.name)
                                    rec.send_notification(rec.user_id, msg, "Блокировка задания. Нет ответа.")
                                    rec.notifications_history += '%s\tAgreement blocked note\n' % str(now)
                            else:
                                msg_text += u"исполнителя"
                                rec.send_notification(rec.user_executor_id, msg_text, subject)
                                rec.send_notification(rec.user_id, msg_text, subject)  # ОЗП
                        if rec.user_approver_id and not rec.approved_by_approver:
                            approver_blockers = rec.get_blocking_users(rec.user_approver_id)
                            if approver_blockers:
                                period = (now.replace(tzinfo=None) - datetime.strptime(approver_blockers.create_date, '%Y-%m-%d %H:%M:%S')).days
                                if period > 0 and 'Agreement blocked note' not in rec.notifications_history:
                                    msg = "Вопрошаемый не отвечает. Спрашивал подтверждающий: %s. Вопрос задан: %s" % (approver_blockers.set_by_id.name, approver_blockers.user_id.name)
                                    rec.send_notification(rec.user_id, msg, "Блокировка задания. Нет ответа.")
                                    rec.notifications_history += '%s\tAgreement blocked note\n' % str(now)
                            else:
                                msg_text += u"подтверждающего"
                                rec.send_notification(rec.user_approver_id, msg_text, subject)
                                rec.send_notification(rec.user_id, msg_text, subject)  # ОЗП
                        if rec.user_predicator_id and not rec.approved_by_predicator:
                            predicator_blockers = rec.get_blocking_users(rec.user_predicator_id)
                            if predicator_blockers:
                                period = (now.replace(tzinfo=None) - datetime.strptime(predicator_blockers.create_date, '%Y-%m-%d %H:%M:%S')).days
                                if period > 0 and 'Agreement blocked note' not in rec.notifications_history:
                                    msg = "Вопрошаемый не отвечает. Спрашивал утверждающий: %s. Вопрос задан: %s" % (predicator_blockers.set_by_id.name, predicator_blockers.user_id.name)
                                    rec.send_notification(rec.user_id, msg, "Блокировка задания. Нет ответа.")
                                    rec.notifications_history += '%s\tAgreement blocked note\n' % str(now)
                            else:
                                msg_text += u"утверждающего"
                                rec.send_notification(rec.user_predicator_id, msg_text, subject)
                                rec.send_notification(rec.user_id, msg_text, subject)  # ОЗП
            except Exception as e:
                log.error(rec)
                log.error(e)

    @api.multi
    def send_notification(self, user, msg_text, subject):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        kwargs = {'author_id': 1, 'subtype_id': 2}
        body = """<a href="%s/web#model=res.partner&amp;id=%s" """ % (base_url, user.partner_id.id)
        body += """class="cleaned_o_mail_redirect" data-oe-id="%s" """ % user.partner_id.id
        body += """data-oe-model="res.partner" target="_blank">@%s</a> """ % user.partner_id.name
        body += msg_text
        kwargs['partner_ids'] = [user.partner_id.id]
        message = self.message_post(body=body, subject=subject, message_type="email", **kwargs)
        log.info('Sent message. %s %s %s', self, user.partner_id, message)
        time.sleep(1)

    @api.multi
    @api.returns('self', lambda value: value.id)
    def message_post(self, body='', subject=None, message_type='notification', subtype=None, parent_id=False, attachments=None, content_subtype='html', **kwargs):
        res = super(TaskMod, self).message_post(body=body, subject=subject, message_type=message_type, **kwargs)
        # Set blocking_user_ids
        if self.state == 'agreement':
            if res.author_id == self.user_executor_id.partner_id and self.approved_by_executor is False:
                for r in res.partner_ids:
                    receiver = self.env['res.users'].search([('partner_id', '=', r.id)])
                    new_block = self.env['res.users.blocking'].create(
                        {'user_id': receiver.id,
                         'task_id': self.id,
                         'name': receiver.name,
                         'set_by_id': self.user_executor_id.id,
                         'message_id': res.id})
            elif res.author_id == self.user_predicator_id.partner_id and self.approved_by_predicator is False:
                for r in res.partner_ids:
                    receiver = self.env['res.users'].search([('partner_id', '=', r.id)])
                    new_block = self.env['res.users.blocking'].create(
                        {'user_id': receiver.id,
                         'task_id': self.id,
                         'name': receiver.name,
                         'set_by_id': self.user_predicator_id.id,
                         'message_id': res.id})
            elif res.author_id == self.user_approver_id.partner_id and self.approved_by_approver is False:
                for r in res.partner_ids:
                    receiver = self.env['res.users'].search([('partner_id', '=', r.id)])
                    new_block = self.env['res.users.blocking'].create(
                        {'user_id': receiver.id,
                         'task_id': self.id,
                         'name': receiver.name,
                         'set_by_id': self.user_approver_id.id,
                         'message_id': res.id})
        return res
