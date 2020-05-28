# -*- coding: utf-8 -*-

from openerp import models, fields, api



class Event(models.Model):
    _inherit = 'calendar.event'

    approver_id = fields.Many2one('res.users', u'Утверждающий', select=True, track_visibility='onchange', ondelete='set null')
    user_plan_id = fields.Many2one('res.users', u'Ответственный за планирование', select=True, track_visibility='onchange', ondelete='set null')
    project_id = fields.Many2one('project.project', u'Связанный проект', select=True, ondelete='set null')
    problem_id = fields.Many2one('kro.problem', u'Связанная проблема', select=True, ondelete='set null')
    aim_id = fields.Many2one('kro.aim', u'Связанная цель', select=True, ondelete='set null')
    task_id = fields.Many2one('project.task', u'Связанная задача', select=True, ondelete='set null')
    points = fields.Text(u'Цели')
    expectations = fields.Text(u'Требуемые результаты')
    state = fields.Selection([('plan', u'Планирование'),
                              ('agreement', u'Согласование'),
                              ('set', u'Назначена'),
                              ('agreed', u'Утверждение'),
                              ('done', u'Проведена'),
                              ('approved', u'Утверждена'),
                              ('closed', u'Завершена'),
                              ], u'Статус',  default='plan')