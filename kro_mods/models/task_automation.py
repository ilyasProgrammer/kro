# -*- coding: utf-8 -*-

from openerp import models, api, fields
import logging
import re
import time
import math
import pytz
from business_duration import businessDuration
from datetime import datetime

log = logging.getLogger(__name__)
DONE_STAGES = ['stating', 'stated', 'approvement', 'approved', 'finished']
STATES = [('plan', u'Планирование'),
          ('agreement', u'Согласование'),
          ('assigned', u'Назначено'),
          ('execution', u'Выполнение'),
          ('stating', u'Утверждение'),
          ('stated', u'Утверждено'),
          ('approvement', u'Подтверждение'),
          ('approved', u'Подтверждено'),
          ('finished', u'Завершено'),
          ('correction', u'Коррекция'),
          ]


class TaskMod(models.Model):
    _inherit = 'project.task'
    
    # PLAN
    @api.model
    def cron_task_automation_plan(self):
        # plan = self.env['project.task'].search([('state', '=', 'plan'), ('user_id', 'in', [43, 98, 91, 66, 149])])
        log.info("Started cron")
        now = datetime.now(pytz.timezone(self.env.context.get('tz') or 'UTC'))
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        kwargs = {'author_id': 1, 'subtype_id': 2}
        plan = self.env['project.task'].search([('state', '=', 'plan'), ('date_start', '<', now), ('date_end_ex', '!=', False)])
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
                    if rec.ngot('PLAN START SOON 1 note'):
                        rec.notifications_history += '%s\tPLAN START SOON 1 note\n' % str(now)
                    elif rec.ngot('PLAN START SOON 2 note'):
                        rec.notifications_history += '%s\tPLAN START SOON 2 note\n' % str(now)
                    elif rec.ngot('PLAN START SOON 3 note'):
                        rec.notifications_history += '%s\tPLAN START SOON 3 note\n' % str(now)
                    elif rec.ngot('PLAN START SOON 4 note'):
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
                if date_diff > 31 and rec.ngot('PLAN 1 note'):
                    msg_text = u"Прошу вывести задание из планирования или, если задание не актуально, то его завершить."
                    subject = u"Планирование > 31 дня"
                    rec.notifications_history += '%s\tPLAN 1 note\n' % str(now)
                elif rec.get_note_period(now, 'PLAN 1 note') > 2 and rec.ngot('PLAN 2 note'):
                    subject = u"Планирование > 34 дней"
                    msg_text = u"При отсутствии ответа в течении 3х дней, с момента получения письма, задание автоматически перейдет в статус завершено."
                    rec.notifications_history += '%s\tPLAN 2 note\n' % str(now)
                elif rec.get_note_period(now, 'PLAN 2 note') > 2 and rec.ngot('PLAN 3 note'):
                    subject = u"Планирование > 40 дней"
                    msg_text = u"Задание завершено."
                    rec.notifications_history += '%s\tPLAN 3 note\n' % str(now)
                    rec.state = 'finished'
                elif len(rec.depend_on_ids) > 0 and rec.all_prev_tasks_are_done():
                    if rec.ngot('PLAN 1 depend on note'):
                        subject = u"Предыдущие задачи утверждаются"
                        msg_text = u"Прошу вывести задание."
                        rec.notifications_history += '%s\tPLAN 1 depend on note\n' % str(now)
                    elif rec.ngot('PLAN 2 depend on note'):
                        if rec.get_note_period(now, 'PLAN 1 depend on note') > 2:
                            subject = u"Предыдущие задачи утверждаются"
                            msg_text = u"Прошу вывести задание 2й раз."
                            rec.notifications_history += '%s\tPLAN 2 depend on note\n' % str(now)
                    elif rec.ngot('PLAN depend on 14 days note'):
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
    
    # AGREEMENT
    @api.model
    def cron_task_automation_agreement(self):
        log.info("Started cron")
        agreement_tasks = self.env['project.task'].search([('state', '=', 'agreement'),
                                                           ('date_start', '!=', False), ('date_end_ex', '!=', False)])
        log.info("Agreement tasks: %s", agreement_tasks)
        if agreement_tasks:
            agreement_tasks.process_agreement_tasks()
        log.info("Finished cron")

    @api.multi
    def process_agreement_tasks(self):
        olga = self.env['res.users'].browse(66)
        now_utc = datetime.now(pytz.timezone('UTC')).replace(tzinfo=None).replace(microsecond=0)
        for rec in self:
            try:
                if rec.is_agreed():
                    rec.state = 'assigned'
                    rec.send_notification(rec.user_executor_id, "Прошу перейти в выполнение", u"Перейти в выполнение")
                    if rec.ngot('Assigned 1'):
                        rec.history_record('Assigned 1')
                    self.env.cr.commit()
                    continue
                elif rec.got('Agreement blocked'):  # TODO filter it initially
                    continue
                elif rec.got('Agreement no action'):  # TODO filter it initially
                    continue
                elif rec.got('Agreement expired by supervisor'):  # TODO filter it initially
                    continue
                elif rec.got('Agreement executors supervisor assigned'):
                    if rec.get_note_bushours_period('Agreement executors supervisor assigned') > 24:
                        if rec.user_executor_id and not rec.approved_by_executor:
                            rec.send_notification(olga, u"Просрочено руководителем", u"Просрочено руководителем")
                            rec.history_record('Agreement expired by supervisor')
                elif rec.got('Agreement approver supervisor assigned'):
                    if rec.get_note_bushours_period('Agreement approver supervisor assigned') > 24:
                        if rec.user_approver_id and not rec.approved_by_approver:
                            rec.send_notification(olga, u"Просрочено руководителем", u"Просрочено руководителем")
                            rec.history_record('Agreement expired by supervisor')
                elif rec.got('Agreement predicator supervisor assigned'):
                    if rec.get_note_bushours_period('Agreement predicator supervisor assigned') > 24:
                        if rec.user_predicator_id and not rec.approved_by_predicator:
                            rec.send_notification(olga, u"Просрочено руководителем", u"Просрочено руководителем")
                            rec.history_record('Agreement expired by supervisor')
                elif rec.got('Agreement 2'):
                    if rec.get_note_bushours_period('Agreement 2') > 24:
                        if rec.user_executor_id and not rec.approved_by_executor:
                            executor_blockers = rec.get_blocking_users(rec.user_executor_id)
                            if executor_blockers:
                                period = businessDuration(t(executor_blockers.create_date), now_utc, unit='hour')
                                if period > 24 and rec.ngot('Agreement blocked'):
                                    msg = u"Вопрошаемый не отвечает. Спрашивал исполнитель: %s. Вопрос задан: %s" % (executor_blockers.set_by_id.name, executor_blockers.user_id.name)
                                    rec.send_notification(rec.user_id, msg, u"Блокировка задания. Нет ответа.")
                                    rec.history_record('Agreement blocked')
                            else:
                                # last_answer = rec.get_last_answered_block(rec.user_executor_id)
                                last_answer = False
                                if last_answer:
                                    period = businessDuration(t(last_answer.answer_date), now_utc, unit='hour')
                                    if period > 24:
                                        if rec.user_executor_id.manager_id:
                                            rec.user_executor_id = rec.user_executor_id.manager_id
                                            msg = u"""Исполнитель заменен на его руководителя.  Иполнитель задал вопрос. На него был дан ответ. 
                                                      Прошло больше одного рабочего дня. Исполнитель не согласовал и не задал новых вопросов."""
                                            rec.send_notification(rec.user_id, msg, u"Автозамена исполнителя")  # ОЗП
                                            rec.history_record('Agreement executors supervisor assigned')
                                        else:
                                            msg = u"""Сроки согласования просрочены и у исполнителя нет руководителя. Задание заблокировано.
                                                      Иполнитель задал вопрос. На него был дан ответ. Прошло больше одного рабочего дня. 
                                                      Исполнитель не согласовал и не задал новых вопросов."""
                                            rec.send_notification(rec.user_id, msg, "Нет руководителя у исполнителя")  # ОЗП
                                            rec.history_record('Agreement blocked\texecutor')
                                    else:
                                        pass  # Последний ответ был < 24 назад. Еще есть время среагировать
                                else:
                                    if rec.user_executor_id.manager_id:
                                        rec.user_executor_id = rec.user_executor_id.manager_id
                                        rec.send_notification(rec.user_id, u"Исполнитель заменен на его руководителя. Нет согласования больше 3х рабочих дней.", u"Автозамена исполнителя")  # ОЗП
                                        rec.history_record('Agreement executors supervisor assigned')
                                    else:
                                        msg = u"""Сроки согласования просрочены и у исполнителя нет руководителя. Задание заблокировано."""
                                        rec.send_notification(rec.user_id, msg, u"Нет руководителя у исполнителя")  # ОЗП
                                        rec.history_record('Agreement blocked\texecutor')
                        if rec.user_approver_id and not rec.approved_by_approver:
                            if rec.user_approver_id.manager_id:
                                rec.user_approver_id = rec.user_approver_id.manager_id
                                rec.send_notification(rec.user_id, u"Подтверждающий заменен на его руководителя. Нет согласования больше 3х рабочих дней.", u"Автозамена подтверждающего")  # ОЗП
                                rec.history_record('Agreement approver supervisor assigned')
                            else:
                                msg = u"""Сроки согласования просрочены и у подтверждающего нет руководителя. Задание заблокировано."""
                                rec.send_notification(rec.user_id, msg, u"Нет руководителя у подтверждающего")  # ОЗП
                                rec.history_record('Agreement blocked\tapprover')
                        if rec.user_predicator_id and not rec.approved_by_predicator:
                            if rec.user_predicator_id.manager_id:
                                rec.user_predicator_id = rec.user_predicator_id.manager_id
                                rec.send_notification(rec.user_id, u"Утверждающий заменен на его руководителя. Нет согласования больше 3х рабочих дней.", u"Автозамена утверждающего")  # ОЗП
                                rec.history_record('Agreement predicator supervisor assigned')
                            else:
                                msg = u"""Сроки согласования просрочены и у утверждающего нет руководителя. Задание заблокировано."""
                                rec.send_notification(rec.user_id, msg, u"Нет руководителя у утверждающего")  # ОЗП
                                rec.history_record('Agreement blocked\tpredicator')
                elif rec.ngot('Agreement 1'):
                    msg_text = u"Прошу согласовать в течение 24 часов."
                    subject = u"Согласование"
                    rec.history_record('Agreement 1')
                    if rec.user_executor_id and not rec.approved_by_executor:
                        rec.send_notification(rec.user_executor_id, msg_text, subject)
                    if rec.user_approver_id and not rec.approved_by_approver:
                        rec.send_notification(rec.user_approver_id, msg_text, subject)
                    if rec.user_predicator_id and not rec.approved_by_predicator:
                        rec.send_notification(rec.user_predicator_id, msg_text, subject)
                elif rec.got('Agreement 1'):
                    if rec.get_note_bushours_period('Agreement 1') > 24:
                        if rec.user_executor_id and not rec.approved_by_executor:
                            executor_blockers = rec.get_blocking_users(rec.user_executor_id)
                            if executor_blockers:
                                period = businessDuration(t(executor_blockers.create_date), now_utc, unit='hour')
                                if period > 24 and rec.ngot('Agreement blocked'):
                                    msg = u"Вопрошаемый не отвечает. Спрашивал исполнитель: %s. Вопрос задан: %s" % (executor_blockers.set_by_id.name, executor_blockers.user_id.name)
                                    rec.send_notification(rec.user_id, msg, u"Блокировка задания. Нет ответа.")
                                    rec.history_record('Agreement blocked')
                                else:
                                    pass  # Вопрос задан < 24 часов назад. Еще есть время ответить
                            else:
                                last_answer = False
                                # last_answer = rec.get_last_answered_block(rec.user_executor_id)
                                if last_answer:
                                    period = businessDuration(t(last_answer.answer_date), now_utc, unit='hour')
                                    if period > 24:
                                        msg_text = u"""Задание не согласовывается, прошу сменить исполнителя. Иполнитель задал вопрос. На него был дан ответ. 
                                                       Прошло больше одного рабочего дня. Исполнитель не согласовал и не задал новых вопросов."""
                                        subject = u"Согласование просрочено"
                                        rec.send_notification(rec.user_executor_id, msg_text, subject)
                                        rec.send_notification(rec.user_id, msg_text, subject)  # ОЗП
                                        rec.history_record('Agreement 2\texecutor')
                                    else:
                                        pass  # Последний ответ был < 24 назад. Еще есть время среагировать
                                else:
                                    msg_text = u"Задание не согласовывается. Исполнитель не проявляет активности больше 1 рабочего дня. Просьба сменить исполнителя."
                                    subject = u"Согласование просрочено. Прошло 48 часов."
                                    rec.send_notification(rec.user_executor_id, msg_text, subject)
                                    rec.send_notification(rec.user_id, msg_text, subject)  # ОЗП
                                    rec.history_record('Agreement 2\texecutor')
                        if rec.user_approver_id and not rec.approved_by_approver:
                            msg_text = u"Задание не согласовывается. Подтверждающий не проявляет активности больше 1 рабочего дня."
                            subject = u"Согласование просрочено. Прошло 48 часов."
                            rec.send_notification(rec.user_approver_id, msg_text, subject)
                            rec.send_notification(rec.user_id, msg_text, subject)  # ОЗП
                            rec.history_record('Agreement 2\tapprover')
                        if rec.user_predicator_id and not rec.approved_by_predicator:
                            msg_text = u"Задание не согласовывается. Утверждающий не проявляет активности больше 1 рабочего дня."
                            subject = u"Согласование просрочено. Прошло 48 часов."
                            rec.send_notification(rec.user_predicator_id, msg_text, subject)
                            rec.send_notification(rec.user_id, msg_text, subject)  # ОЗП
                            rec.history_record('Agreement 2\tpredicator')
                self.env.cr.commit()
            except Exception as e:
                log.error(rec)
                log.error(e)

    # ASSIGNED
    @api.model
    def cron_task_automation_assigned(self):
        log.info("Started cron")
        now = datetime.now(pytz.timezone(self.env.context.get('tz') or 'UTC'))
        assigned = self.env['project.task'].search([('state', '=', 'assigned'),
                                                    ('date_start', '<', now), ('date_end_ex', '!=', False)])
        log.info("Assigned tasks: %s", assigned)
        assigned.process_assigned_tasks()
        log.info("Finished cron")

    @api.multi
    def process_assigned_tasks(self):
        now_utc = datetime.now(pytz.timezone('UTC')).replace(tzinfo=None).replace(microsecond=0)
        for rec in self:
            try:
                if rec.got('Assigned 3'):
                    continue
                elif rec.ngot('Assigned 1'):
                    rec.send_notification(rec.user_executor_id, u"Прошу перейти в выполнение.", u"Перейти в выполнение")
                    rec.history_record('Assigned 1')
                elif rec.got('Assigned 1') and rec.ngot('Assigned 2'):
                    if rec.get_note_bushours_period('Agreement 1') > 24:
                        rec.send_notification(rec.user_executor_id, u"Прошу перейти в выполнение 2й раз.", u"Перейти в выполнение. Повторно.")
                        rec.history_record('Assigned 2')
                elif rec.got('Assigned 2') and rec.ngot('Assigned 3'):
                    if rec.get_note_bushours_period('Agreement 2') > 24:
                        msg = u"Действий нет, прошу сменить исполнителя."
                        rec.send_notification(rec.user_id, msg, u"Назначено. Нет действий.")  # ОЗП
                        if rec.user_executor_id.manager_id:
                            rec.send_notification(rec.user_executor_id.manager_id, msg, u"Назначено. Нет действий.")
                        rec.history_record('Assigned 3')
            except Exception as e:
                log.error(rec)
                log.error(e)

    # EXECUTION
    @api.model
    def cron_task_automation_execution(self):
        log.info("Started cron")
        now = datetime.now(pytz.timezone(self.env.context.get('tz') or 'UTC'))
        execution = self.env['project.task'].search([('state', '=', 'execution'), ('date_start', '!=', False), ('date_end_ex', '!=', False)])
        log.info("Execution tasks: %s", execution)
        execution.process_execution_tasks()
        log.info("Finished cron")
        
    @api.multi
    def process_execution_tasks(self):
        now_utc = datetime.now(pytz.timezone('UTC')).replace(tzinfo=None).replace(microsecond=0)
        for rec in self:
            try:
                if rec.got('Execution 3'):
                    continue
                elif rec.ngot('Execution 1'):
                    period = businessDuration(now_utc, t(rec.date_end_ex), unit='hour')
                    if period < 25:
                        rec.send_notification(rec.user_executor_id, u"Разрешите Вам напомнить, что завтра дата выполнения задания заканчивается.", u"Выполнение")
                        rec.history_record('Execution 1')
                    elif period < 1 or math.isnan(period):
                        rec.send_notification(rec.user_executor_id, u"Задание просрочено, срок выполнения истек. Прошу перевести в утверждение.", u"Выполнение")
                        rec.history_record('Execution 1')
                elif rec.ngot('Execution 2'):
                    period = businessDuration(t(rec.date_end_ex), now_utc, unit='hour')
                    if period > 0:
                        msg = u"Задание просрочено, срок выполнения истек. Прошу перевести в утверждение, если задание выполнено или указать срок выполнения со вторым переносом и причину переноса. Третий срок переноса недопустим"
                        rec.send_notification(rec.user_executor_id, msg, u"Выполнение просрочено")
                        rec.history_record('Execution 2')
                elif rec.got('Execution 2') and rec.ngot('Execution 3'):
                    period = businessDuration(t(rec.date_end_ex), now_utc, unit='hour')
                    if period > 24:
                        msg = u"Сроки выполнения нарушены. Прошу перепланировать"
                        rec.send_notification(rec.user_id, msg, u"Выполнение просрочено ")
                        rec.history_record('Execution 3')
                time.sleep(1)
            except Exception as e:
                log.error(rec)
                log.error(e)

    # Other
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
    def get_note_bushours_period(self, note):
        # now and dates in notifications_history are UTC+5
        now_ekt = datetime.now(pytz.timezone('Asia/Yekaterinburg')).replace(tzinfo=None)
        for l in self.notifications_history.splitlines():
            if l.split('\t')[1] == note:
                notification_moment = datetime.strptime(l.split('\t')[0][:19], '%Y-%m-%d %H:%M:%S')
                res = businessDuration(notification_moment, now_ekt, unit='hour')
                return res
        return 0
  
    @api.multi
    def get_blocking_users(self, user_id):
        for b in self.blocking_user_ids.sorted(key=lambda r: r.id, reverse=True):  # Take last one
            if b.set_by_id == user_id and not b.answered:
                return b
        return False

    @api.multi
    def get_last_answered_block(self, user_id):
        for b in self.blocking_user_ids.sorted(key=lambda r: r.id, reverse=True):  # Take last one
            if b.set_by_id == user_id and b.answered:
                return b
        return False
    
    @api.multi
    def is_agreed(self):
        self.ensure_one()
        if self.user_executor_id and self.user_predicator_id and self.user_approver_id:
            if self.approved_by_executor and self.approved_by_predicator and self.approved_by_approver:
                return True
        elif self.user_executor_id and self.user_predicator_id:
            if self.approved_by_executor and self.approved_by_predicator:
                return True
        elif self.user_executor_id and self.user_approver_id:
            if self.approved_by_executor and self.approved_by_approver:
                return True
        elif self.user_executor_id and self.approved_by_executor:
            return True
        return False

    @api.multi
    def history_record(self, msg):
        now_ekt = datetime.now(pytz.timezone('Asia/Yekaterinburg')).replace(tzinfo=None).replace(microsecond=0)
        for rec in self:
            rec.notifications_history += '%s\t%s\n' % (str(now_ekt), msg)

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
    def message_post(self, body='', subject=None, **kwargs):
        res = super(TaskMod, self).message_post(body=body, subject=subject, **kwargs)
        # Set blocking_user_ids
        if self.state == 'agreement':
            set_by_id = None
            if res.author_id == self.user_executor_id.partner_id and self.approved_by_executor is False:
                set_by_id = self.user_executor_id.id
            elif res.author_id == self.user_predicator_id.partner_id and self.approved_by_predicator is False:
                set_by_id = self.user_predicator_id.id
            elif res.author_id == self.user_approver_id.partner_id and self.approved_by_approver is False:
                set_by_id = self.user_approver_id.id
            if set_by_id and "model=res.partner&amp;id=" in res.body and len(res.body.split('data-oe-id="')) > 1:
                partner_id = int(res.body.split('data-oe-id="')[1].split('" data-oe-model')[0])
                receiver = self.env['res.users'].search([('partner_id', '=', partner_id)])
                new_block = self.env['res.users.blocking'].create({'user_id': receiver.id,
                                                                   'task_id': self.id,
                                                                   'name': receiver.name,
                                                                   'set_by_id': set_by_id,
                                                                   'message_id': res.id})
        return res

    @api.multi
    def got(self, note):
        if self.notifications_history is False:
            self.notifications_history = ''
            return False
        if note in self.notifications_history:
            return True
        else:
            return False

    @api.multi
    def ngot(self, note):
        if self.notifications_history is False:
            self.notifications_history = ''
            return True
        if note in self.notifications_history:
            return False
        else:
            return True


def t(time_str):
    if len(time_str) == 10:
        return datetime.strptime(time_str, '%Y-%m-%d')
    return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')


def d(time_str):
    return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S').date()
