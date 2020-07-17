# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
import datetime
import pytz

class Project(models.Model):
    _inherit = 'project.project'
    problem_ids = fields.One2many('kro.problem', 'kro_project_id', ondelete='set null',  string=u'Проблемы')
    use_tasks = fields.Boolean(default=False)
    private = fields.Boolean(default=False, string=u'Приватный')
    project_id = fields.Many2one('project.project', u'Проект родитель', ondelete="set null")
    project_ids = fields.One2many('project.project', 'project_id', ondelete="set null")


class Problem(models.Model):
    _name = 'kro.problem'
    _inherit = 'project.task'
    _description = u"Проблема"
    _display_name = u"Проблема"
    name = fields.Char(string=u'Наименование',track_visibility='onchange', size=128, required=True, select=True)
    kro_project_id = fields.Many2one('project.project', u'Проект', readonly=True, ondelete="set null")
    date_deadline = fields.Date(u'Плановая дата решения', select=True, copy=False, track_visibility='always')
    fact_date = fields.Date(u'Фактическая дата', select=True, track_visibility='always')
    user_id = fields.Many2one('res.users', u'Инициатор', select=True, track_visibility='onchange', ondelete="set null")
    priority = fields.Selection([('0', u'Низкий'), ('1', u'Средний'), ('2', u'Высокий')], u'Приоритет', select=True, track_visibility='always')
    # user_aim_id = fields.Many2one('res.users', u'Ответственный за определение целей', select=True, track_visibility='onchange', ondelete='set null')
    # user_admin_id = fields.Many2one('res.users', u'Администратор', select=True, track_visibility='onchange')
    addressee_id = fields.Many2one('res.users', u'Адресат', select=True, track_visibility='onchange', ondelete='set null')
    current_user_id = fields.Many2one('res.users', compute='_get_responsible', string=u'Ответственный', track_visibility='always', store=True)
    description = fields.Html(u'Формулировка проблемы', track_visibility='always')
    effects = fields.Text(u'Последствия', track_visibility='always')
    causes = fields.Text(u'Причины', track_visibility='always')
    decision = fields.Text(u'Решение', track_visibility='always')
    reason_aside_problem = fields.Many2one('kro.problem', u'Причина откладывания - проблема', select=True, ondelete='set null', track_visibility='always')
    reason_aside_aim = fields.Many2one('kro.aim', u'Причина откладывания - цель', select=True, ondelete='set null', track_visibility='always')
    reason_aside_task = fields.Many2one('project.task', u'Причина откладывания - задача', select=True, ondelete='set null', track_visibility='always')
    reason_correction = fields.Text(u'Причина коррекции', track_visibility='always')
    aim_ids = fields.One2many('kro.aim', 'problem_id', ondelete="cascade", string=u'Цели', track_visibility='always')
    # stage_id = fields.Many2one('project.task.type', u'Статус', track_visibility='onchange', select=True, domain="[('project_ids', '=', project_id)]", copy=False),
    state = fields.Selection([('plan', u'Планирование'),
                              ('moved', u'Передана'),
                              ('process', u'Обрабатывается'),
                              ('taken', u'Принята'),
                              ('suspended', u'Отложена'),
                              ('canceled', u'Отклонена'),
                              ('closed', u'Закрыта'),
                              ], u'Статус',  default='plan', track_visibility='always')
    remaining_hours = fields.Boolean()
    effective_hours = fields.Boolean()
    total_hours = fields.Boolean()
    progress = fields.Boolean()
    delay_hours = fields.Boolean()
    timesheet_ids = fields.Boolean()
    analytic_account_id = fields.Boolean()
    admin = fields.Boolean(compute='_compute_fields', default=False, store=False)
    manager = fields.Boolean(compute='_compute_fields', default=False, store=False)
    planner = fields.Boolean(compute='_compute_fields', default=False, store=False)
    obs = fields.Boolean(compute='_compute_fields', default=False, store=False)
    private = fields.Boolean(default=False, string=u'Приватный')

    @api.multi
    def _message_notification_recipients(self, message, recipients):
        result = super(Problem, self)._message_notification_recipients(message, recipients)
        result['group_project_user']['button_access']['title'] = u'Открыть проблему'
        return result

    @api.one
    @api.depends('state', 'addressee_id', 'user_id')
    def _get_responsible(self):
        if self.state in ['plan', 'suspended', 'taken']:
            self.current_user_id = self.user_id
        if self.state in ['moved', 'process']:
            self.current_user_id = self.addressee_id
        if self.state in ['canceled', 'closed']:
            self.current_user_id = None

    @api.one
    def _compute_fields(self):
        self.admin = False
        self.manager = False
        self.planner = False
        self.obs = False
        self.manager = True if self._uid in [r.id for r in self.env.ref('project.group_project_manager').users] else False
        self.admin = True if self._uid in [r.id for r in self.env.ref('kro.group_adm_bp').users] else False
        if self.admin or self.manager:
            self.planner = True
        if self._uid == self.user_id.id:
            self.planner = True
        if self._uid == self.addressee_id.id:
            self.obs = True

    @api.model
    def default_get(self, fields):
        res = super(Problem, self).default_get(fields)
        res['manager'] = True
        res['admin'] = True
        res['planner'] = True
        res['executor'] = True
        res['predicator'] = True
        res['approver'] = True
        return res

    @api.model
    def _store_history(self, ids):
        if 1:
            return False
        return True

    @api.model
    def _hours_get(self, ids):
        return

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'user_id' in init_values and self.user_id:  # assigned -> new
            return 'kro.mt_problem_new'
        return super(Problem, self)._track_subtype(init_values)

    def _notification_get_recipient_groups(self, cr, uid, ids, message, recipients, context=None):
        res = super(Problem, self)._notification_get_recipient_groups(cr, uid, ids, message, recipients, context=context)
        take_action = self._notification_link_helper(cr, uid, ids, 'assign', context=context)
        new_action_id = self.pool['ir.model.data'].xmlid_to_res_id(cr, uid, 'kro.action_problems')
        new_action = self._notification_link_helper(cr, uid, ids, 'new', context=context, action_id=new_action_id)
        task_record = self.browse(cr, uid, ids[0], context=context)
        actions = []
        if not task_record.user_id:
            actions.append({'url': take_action, 'title': _('I take it')})
        else:
            actions.append({'url': new_action, 'title': _('Новая проблема')})
        res['group_project_user'] = {
            'actions': actions
        }
        return res

    @api.model
    def create(self, vals):
        if vals['kro_project_id']:
            project = self.env['project.project'].browse(vals['kro_project_id'])
            vals['private'] = project.private
        subs = []
        addressee = self.env['res.users'].browse(vals['addressee_id'])
        user = self.env['res.users'].browse(vals['user_id'])
        vals['message_follower_ids'] = []
        if addressee.partner_id and addressee != user:
            subs += self.env['mail.followers']._add_follower_command(self._name, [], {addressee.partner_id.id: None}, {}, force=True)[0]
        problem_users = self.env.ref('kro.group_problem_subscribers').users
        if len(problem_users):
            for usr in problem_users:
                if usr != user:
                    pass
                    # subs += self.env['mail.followers']._add_follower_command(self._name, [], {usr.partner_id.id: None}, {}, force=True)[0]
        unique_subs = make_unique(subs)
        vals['message_follower_ids'] = unique_subs
        return super(Problem, self).create(vals)

    @api.multi
    def get_formview_id(self):
        return self.env.ref('kro.kro_problem_form').id


class Aim(models.Model):
    _name = 'kro.aim'
    _inherit = 'project.task'
    _description = u"Цель"
    _order = 'code'
    code = fields.Char(string=u'Цель № ', required=True, default="/")
    date_start = fields.Date(string=u'Дата начала', compute='_time_count', store=True)
    date_end = fields.Date(string=u'Дата завершения', compute='_time_count', store=True)
    problem_id = fields.Many2one('kro.problem', u'Проблема', ondelete='set null')
    project_id = fields.Many2one('project.project', string=u'Проект', ondelete='set null', help=u'Проект для прямой привязки')
    problem_project_id = fields.Many2one(related='problem_id.kro_project_id', string=u'Проект', ondelete='set null', readonly=True, help=u'Проект от проблемы')
    priority = fields.Selection([('0', u'Низкий'), ('1', u'Средний'), ('2', u'Высокий')], u'Приоритет', select=True, track_visibility='always')
    reason_aside_problem = fields.Many2one('kro.problem', u'Причина откладывания - проблема', select=True, ondelete='set null', track_visibility='always')
    reason_aside_aim = fields.Many2one('kro.aim', u'Причина откладывания - цель', select=True, ondelete='set null', track_visibility='always')
    reason_aside_task = fields.Many2one('project.task', u'Причина откладывания - задача', select=True, ondelete='set null', track_visibility='always')
    reason_correction = fields.Text(u'Причина коррекции', track_visibility='always')
    user_id = fields.Many2one('res.users', u'Ответственный за планирование', select=True, track_visibility='onchange', ondelete="set null")
    current_user_id = fields.Many2one('res.users', compute='_get_responsible', string=u'Ответственный', track_visibility='always', store=True)
    job_ids = fields.One2many('kro.job', 'aim_id', ondelete="cascade", string=u'Задачи', track_visibility='always')
    task_ids = fields.One2many('project.task', 'aim_id', ondelete="cascade", string=u'Задания', track_visibility='always')
    task_count = fields.Integer(compute='_task_count')
    state = fields.Selection([('plan', u'Планирование'),
                              ('defined', u'Определена'),
                              ('corrections', u'Коррекция'),
                              ('finished', u'Завершена'),
                              ], u'Статус', readonly=True, default='plan', track_visibility='always')
    remaining_hours = fields.Boolean()
    effective_hours = fields.Boolean()
    total_hours = fields.Boolean()
    planned_hours = fields.Float(compute='_time_count', string=u'Запланированно часов всего')
    total_time = fields.Integer(compute='_time_count', string=u'Затраченно часов всего')
    progress = fields.Float(compute='_time_count', string=u'Прогресс')
    delay_hours = fields.Boolean()
    timesheet_ids = fields.Boolean()
    analytic_account_id = fields.Boolean()
    _sql_constraints = [
        ('kro_aim_unique_code', 'UNIQUE (code)',
         _('The code must be unique!')),
    ]
    private = fields.Boolean(default=False, string=u'Приватный')

    @api.multi
    def _message_notification_recipients(self, message, recipients):
        result = super(Aim, self)._message_notification_recipients(message, recipients)
        result['group_project_user']['button_access']['title'] = u'Открыть цель'
        return result

    @api.one
    @api.depends('state', 'user_id')
    def _get_responsible(self):
        admins = self.env.ref('kro.group_adm_bp').users
        if len(admins) and self.state in ['defined']:
            self.current_user_id = admins[0]
        else:
            self.current_user_id = self.user_id

    @api.one
    @api.depends('job_ids', 'task_ids')
    def _time_count(self):
        planned_hours = 0
        total_time = 0
        planned_hours += sum([r.planned_hours for r in self.task_ids])
        total_time += sum([r.effective_hours for r in self.task_ids])
        for rec in self.job_ids:
            planned_hours += sum([r.planned_hours for r in rec.task_ids])
            total_time += sum([r.effective_hours for r in rec.task_ids])
        if total_time and planned_hours:
            self.planned_hours = planned_hours
            self.total_time = total_time
            self.progress = round(min(100.0 * total_time / planned_hours, 99.99), 2)
        start_dates = [datetime.datetime.strptime(r.date_start, '%Y-%m-%d') for r in self.task_ids if r.date_start is not False]
        end_dates = [datetime.datetime.strptime(r.date_end, '%Y-%m-%d') for r in self.task_ids if r.date_end is not False]
        start_dates += [datetime.datetime.strptime(r.date_start, '%Y-%m-%d') for r in self.job_ids if r.date_start is not False]
        end_dates += [datetime.datetime.strptime(r.date_end, '%Y-%m-%d') for r in self.job_ids if r.date_end is not False]
        if len(start_dates):
            self.date_start = min(start_dates)
        if len(end_dates):
            self.date_end = max(end_dates)
        if self.total_time and self.planned_hours:
            self.progress = round(min(100.0 * self.total_time / self.planned_hours, 99.99), 2)

    @api.model
    def action_tasks(self, active_id):
        search_view = self.env['ir.model.data'].get_object_reference('kro', 'kro_aim_all_tasks')
        view_id = self.env['ir.model.data'].get_object_reference('kro', 'kro_aims_task_search_form')
        aim = self.env['kro.aim'].browse(active_id)
        job_tasks_ids = []
        for r in aim.job_ids:
            for t in r.task_ids:
                job_tasks_ids.append(t.id)
        value = {
            'domain': [('id', 'in', [rec.id for rec in aim.task_ids]+job_tasks_ids)],
            'view_type': 'form',
            'view_mode': 'search,tree,form',
            'res_model': 'project.task',
            'res_id': False,
            'view_id': False,
            'context': {},
            'type': 'ir.actions.act_window',
            # 'target': 'inlineview',
            'search_view_id': search_view and search_view[1] or False
        }
        return value

    @api.one
    def _task_count(self):
        job_tasks_ids = []
        for r in self.job_ids:
            for t in r.task_ids:
                job_tasks_ids.append(t.id)
        self.task_count = len(self.task_ids.ids+job_tasks_ids)

    @api.model
    def _store_history(self, ids):
        if 1:
            return False
        return True

    @api.model
    def _hours_get(self, ids):
        return

    @api.model
    def _track_subtype(self, init_values):
        if 'user_id' in init_values and self.user_id:  # assigned -> new
            return 'kro.mt_aim_new'
        return super(Aim, self)._track_subtype(init_values)

    def _notification_get_recipient_groups(self, cr, uid, ids, message, recipients, context=None):
        res = super(Aim, self)._notification_get_recipient_groups(cr, uid, ids, message, recipients, context=context)
        take_action = self._notification_link_helper(cr, uid, ids, 'assign', context=context)
        new_action_id = self.pool['ir.model.data'].xmlid_to_res_id(cr, uid, 'kro.action_aims')
        new_action = self._notification_link_helper(cr, uid, ids, 'new', context=context, action_id=new_action_id)
        task_record = self.browse(cr, uid, ids[0], context=context)
        actions = []
        if not task_record.user_id:
            actions.append({'url': take_action, 'title': _('I take it')})
        else:
            actions.append({'url': new_action, 'title': _('Новая цель')})
        res['group_project_user'] = {
            'actions': actions
        }
        return res

    @api.model
    def create(self, vals):
        if vals['problem_id']:
            problem = self.env['kro.problem'].browse(vals['problem_id'])
            vals['private'] = problem.private
        if vals.get('code', '/') == '/':
            vals['code'] = self.env['ir.sequence'].next_by_code('kro.aim')
        return super(Aim, self).create(vals)

    @api.one
    def copy(self, default=None):
        if default is None:
            default = {}
        default['code'] = self.env['ir.sequence'].next_by_code('kro.aim')
        return super(Aim, self).copy(default)

    @api.multi
    def get_formview_id(self):
        return self.env.ref('kro.kro_aim_form').id


class Job(models.Model):
    _name = 'kro.job'
    _inherit = 'project.task'
    _description = u'Задача'
    _order = 'code'
    code = fields.Char(string=u'Номер', required=True, default="/")
    date_start = fields.Date(string=u'Дата начала', compute='_time_count', store=True)
    date_end = fields.Date(string=u'Дата завершения', compute='_time_count', store=True)
    priority = fields.Selection([('0', u'Низкий'), ('1', u'Средний'), ('2', u'Высокий')], u'Приоритет', select=True, track_visibility='always')
    aim_id = fields.Many2one('kro.aim', u'Цель', ondelete='set null', track_visibility='always')
    problem_id = fields.Many2one(related='aim_id.problem_id', string=u'Проблема', readonly=True, ondelete="set null")
    project_id = fields.Many2one(related='problem_id.kro_project_id', string=u'Проект', readonly=True, ondelete='set null')
    aim_project_id = fields.Many2one(related='aim_id.project_id', string=u'Проект', readonly=True, ondelete='set null', help='Проект напрямую привязанный к цели')
    user_id = fields.Many2one('res.users', u'Ответственный за планирование', select=True, track_visibility='onchange', ondelete="set null")
    current_user_id = fields.Many2one('res.users', compute='_get_responsible', string=u'Ответственный', track_visibility='always', store=True)
    task_ids = fields.One2many('project.task', 'job_id', ondelete="cascade", string=u'Задания', track_visibility='always')
    task_count = fields.Integer(compute='_task_count', string=u'Количество заданий')
    planned_hours = fields.Float(compute='_time_count', string=u'Запланированно часов всего')
    total_time = fields.Integer(compute='_time_count', string=u'Затраченно часов всего')
    reason_aside_problem = fields.Many2one('kro.problem', u'Причина откладывания - проблема', select=True, ondelete='set null', track_visibility='always')
    reason_aside_aim = fields.Many2one('kro.aim', u'Причина откладывания - цель', select=True, ondelete='set null', track_visibility='always')
    reason_aside_task = fields.Many2one('project.task', u'Причина откладывания - задача', select=True, ondelete='set null', track_visibility='always')
    reason_correction = fields.Text(u'Причина коррекции', track_visibility='always')
    state = fields.Selection([('plan', u'Планирование'),
                              ('defined', u'Определена'),
                              ('suspended', u'Отложена'),
                              ('corrections', u'Коррекция'),
                              ('finished', u'Завершена'),
                              ], u'Статус', readonly=True, default='plan', track_visibility='always')
    remaining_hours = fields.Boolean()
    effective_hours = fields.Boolean()
    total_hours = fields.Boolean()
    progress = fields.Float(compute='_time_count', string=u'Прогресс')
    delay_hours = fields.Boolean()
    timesheet_ids = fields.Boolean()
    analytic_account_id = fields.Boolean()
    _sql_constraints = [
        ('kro_job_unique_code', 'UNIQUE (code)',
         _('The code must be unique!')),
    ]
    admin = fields.Boolean(compute='_compute_fields', default=False, store=False)
    manager = fields.Boolean(compute='_compute_fields', default=False, store=False)
    planner = fields.Boolean(compute='_compute_fields', default=False, store=False)
    obs = fields.Boolean(compute='_compute_fields', default=False, store=False)
    private = fields.Boolean(default=False, string=u'Приватный')

    @api.multi
    def _message_notification_recipients(self, message, recipients):
        result = super(Job, self)._message_notification_recipients(message, recipients)
        result['group_project_user']['button_access']['title'] = u'Открыть задачу'
        return result

    @api.one
    @api.depends('state', 'user_id')
    def _get_responsible(self):
        admins = self.env.ref('kro.group_adm_bp').users
        if len(admins) and self.state in ['defined']:
            self.current_user_id = admins[0]
        else:
            self.current_user_id = self.user_id

    @api.one
    def _compute_fields(self):
        self.admin = False
        self.manager = False
        self.planner = False
        self.manager = True if self._uid in [r.id for r in self.env.ref('project.group_project_manager').users] else False
        self.admin = True if self._uid in [r.id for r in self.env.ref('kro.group_adm_bp').users] else False
        self.obs = True if self._uid in [r.id for r in self.env.ref('kro.group_project_obs_max').users] or self._uid in [r.id for r in self.env.ref('kro.group_project_obs').users] else False
        if self.admin or self.manager:
            self.planner = True
        if self._uid == self.user_id.id:
            self.planner = True

    @api.model
    def default_get(self, fields):
        res = super(Job, self).default_get(fields)
        res['manager'] = True
        res['admin'] = True
        res['planner'] = True
        res['executor'] = True
        res['predicator'] = True
        res['approver'] = True
        return res

    @api.one
    def _task_count(self):
        self.task_count = len(self.task_ids.ids)

    @api.one
    @api.depends('task_ids')
    def _time_count(self):
        if len(self.task_ids):
            self.planned_hours = sum([r.planned_hours for r in self.task_ids])
            self.total_time = sum([r.effective_hours for r in self.task_ids])
            start_dates = [datetime.datetime.strptime(r.date_start, '%Y-%m-%d') for r in self.task_ids if r.date_start is not False]
            end_dates = [datetime.datetime.strptime(r.date_end, '%Y-%m-%d') for r in self.task_ids if r.date_end is not False]
            if len(start_dates):
                self.date_start = min(start_dates)
            if len(end_dates):
                self.date_end = max(end_dates)
            if self.total_time and self.planned_hours:
                self.progress = round(min(100.0 * self.total_time / self.planned_hours, 99.99), 2)

    @api.model
    def _store_history(self, ids):
        return True

    @api.model
    def _hours_get(self, ids):
        return

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'user_id' in init_values and self.user_id:  # assigned -> new
            return 'kro.mt_job_new'
        return super(Job, self)._track_subtype(init_values)

    @api.model
    def create(self, vals):
        if vals['aim_id']:
            aim = self.env['kro.aim'].browse(vals['aim_id'])
            vals['private'] = aim.private
        if vals.get('code', '/') == '/':
            vals['code'] = self.env['ir.sequence'].next_by_code('kro.job')
        return super(Job, self).create(vals)

    @api.one
    def copy(self, default=None):
        if default is None:
            default = {}
        default['code'] = self.env['ir.sequence'].next_by_code('kro.job')
        return super(Job, self).copy(default)

    @api.multi
    def get_formview_id(self):
        return self.env.ref('kro.kro_job_form').id

    def _notification_get_recipient_groups(self, cr, uid, ids, message, recipients, context=None):
        res = super(Job, self)._notification_get_recipient_groups(cr, uid, ids, message, recipients, context=context)
        take_action = self._notification_link_helper(cr, uid, ids, 'assign', context=context)
        new_action_id = self.pool['ir.model.data'].xmlid_to_res_id(cr, uid, 'kro.action_job')
        new_action = self._notification_link_helper(cr, uid, ids, 'new', context=context, action_id=new_action_id)
        task_record = self.browse(cr, uid, ids[0], context=context)
        actions = []
        if not task_record.user_id:
            actions.append({'url': take_action, 'title': _('I take it')})
        else:
            actions.append({'url': new_action, 'title': _('Новая задача')})
        res['group_project_user'] = {
            'actions': actions
        }
        return res


class Task(models.Model):
    _inherit = 'project.task'
    _description = u'Задание'
    description = fields.Html(u'Описание', track_visibility='always')
    # date_start_ex = fields.Datetime(u'Старт') используем date_start для гантта
    code = fields.Char(string=u'Номер', required=True, default="/")
    date_end = fields.Date(compute='_set_date_end', track_visibility='always')
    date_start = fields.Date(u'Исполнитель дата начала', track_visibility='always', copy=False)
    date_end_ex = fields.Date(u'Исполнитель дата окончания', track_visibility='onchange')
    date_start_pr = fields.Date(u'Утверждающий дата начала', track_visibility='onchange')
    date_end_pr = fields.Date(u'Утверждающий дата окончания', track_visibility='onchange')
    date_start_ap = fields.Date(u'Подтверждающий дата начала', track_visibility='onchange')
    date_end_ap = fields.Date(u'Подтверждающий дата окончания', track_visibility='always')
    plan_time_ex = fields.Float(u'План по времени исполнитель', track_visibility='onchange')
    plan_time_pr = fields.Float(u'План по времени утверждающий', track_visibility='onchange')
    plan_time_ap = fields.Float(u'План по времени подтверджающий', track_visibility='onchange')
    got_approver = fields.Boolean(u'С подтверждающим', track_visibility='onchange')
    amount = fields.Float(u'Бюджет', track_visibility='onchange')
    # mark_state = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5'),('6','6'),('7','7')], string=u'Оценка статуса', track_visibility='onchange')
    # mark_result = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5'),('6','6'),('7','7')], string=u'Оценка результата', track_visibility='onchange')
    mark_state = fields.Integer(string=u'Оценка статуса', track_visibility='onchange', group_operator='avg')
    mark_result = fields.Integer(string=u'Оценка результата', track_visibility='onchange', group_operator='avg')

    job_id = fields.Many2one('kro.job', string=u'Задача', ondelete="set null", help=u'Задача родитель')
    job_aim_id = fields.Many2one(related='job_id.aim_id', string=u'Цель', readonly=True, help=u'Цель из задачи')
    aim_id = fields.Many2one('kro.aim', string=u'Цель', ondelete="set null" , help=u'Цель для прямой привязки минуя задачу')
    problem_id = fields.Many2one(related='job_aim_id.problem_id', string=u'Проблема', readonly=True, help=u'Проблема из цели из родительской задачи')
    problem_project_id = fields.Many2one(related='job_aim_id.problem_id.kro_project_id', string=u'Проект', readonly=True, help=u'Проект из проблемы из цели из родительской задачи')
    aim_project_id = fields.Many2one(related='job_aim_id.project_id', string=u'Проект', readonly=True, help=u'Проект из цели из родительской задачи (привязанный непосредственно к цели проект минуя проблему)')
    parent_project_id = fields.Many2one(related='job_aim_id.problem_id.kro_project_id.project_id', string=u'Проект родитель', readonly=True, help=u'Проект родитель проекта из проблемы из цели из родительской задачи')

    required_result = fields.Text(u'Требуемый результат', track_visibility='onchange')
    priority = fields.Selection([('0', u'Низкий'), ('1', u'Средний'), ('2', u'Высокий')], u'Приоритет', select=True, track_visibility='onchange')
    user_executor_id = fields.Many2one('res.users', string=u'Исполнитель', ondelete="set null", track_visibility='onchange')
    user_predicator_id = fields.Many2one('res.users', string=u'Утверждающий', ondelete="set null", track_visibility='onchange')
    user_approver_id = fields.Many2one('res.users', string=u'Подтверждающий', ondelete="set null", track_visibility='onchange')
    current_user_id = fields.Many2one('res.users', compute='_get_responsible', string=u'Ответственный', track_visibility='always', store=True)
    approved_by_executor = fields.Boolean(u'Согласовал исполнитель', track_visibility='onchange')
    approved_by_predicator = fields.Boolean(u'Согласовал утверждающий', track_visibility='onchange')
    approved_by_approver = fields.Boolean(u'Согласовал подтверждающий', track_visibility='onchange')
    state = fields.Selection([('plan', u'Планирование'),
                              ('agreement', u'Согласование'),
                              ('assigned', u'Назначено'),
                              ('execution', u'Выполнение'),
                              ('stating', u'Утверждение'),
                              ('stated', u'Утверждено'),
                              ('approvement', u'Подтверждение'),
                              ('approved', u'Подтверждено'),
                              ('finished', u'Завершено'),
                              ('correction', u'Коррекция'),
                              ], u'Статус',  default='plan', track_visibility='onchange')
    planned_hours = fields.Float(compute='_time_count', string=u'Запланированно часов', readonly=True)
    depend_on_ids = fields.Many2many('project.task', relation='depend_on_rel', column1='col_name1', column2='col_name2', string=u'Основание', track_visibility='onchange')
    dependent_ids = fields.Many2many('project.task', relation='dependent_rel', column1='col_name3', column2='col_name4', string=u'Зависимые', track_visibility='onchange')
    progress = fields.Float(compute='_time_count', string=u'Прогресс')
    executor = fields.Boolean(compute='_compute_fields', default=False, store=False, readonly=True)
    predicator = fields.Boolean(compute='_compute_fields', default=False, store=False, readonly=True)
    approver = fields.Boolean(compute='_compute_fields', default=False, store=False, readonly=True)
    planner = fields.Boolean(compute='_compute_fields', default=False, store=False, readonly=True)
    manager = fields.Boolean(compute='_compute_fields', default=False, store=False, readonly=True)
    admin = fields.Boolean(compute='_compute_fields', default=False, store=False, readonly=True)
    doc_count = fields.Integer(compute='_get_attached_docs', string="Количество прикрепленных вложений")
    private = fields.Boolean(default=False, string=u'Приватный')
    blocking_user_ids = fields.One2many('res.users.blocking', 'task_id', string=u'Блокирующие', copy=False)
    state_history = fields.Text(u'История статусов', default="", copy=False)

    @api.multi
    def _message_notification_recipients(self, message, recipients):
        result = super(Task, self)._message_notification_recipients(message, recipients)
        result['group_project_user']['button_access']['title'] = u'Открыть задание'
        return result

    @api.one
    @api.depends('state', 'user_executor_id', 'user_predicator_id', 'user_approver_id', 'user_id')
    def _get_responsible(self):
        admins = self.env.ref('kro.group_adm_bp').users
        if self.state in ['plan', 'stated', 'approved', 'correction']:
            self.current_user_id = self.user_id
        if self.state == 'agreement' and len(admins):
            self.current_user_id = admins[0]
        if self.state in ['assigned', 'execution']:
            self.current_user_id = self.user_executor_id
        if self.state in ['stating']:
            self.current_user_id = self.user_predicator_id
        if self.state in ['approvement']:
            self.current_user_id = self.user_approver_id
        if self.state in ['finished']:
            self.current_user_id = None

    @api.one
    def _get_attached_docs(self):
        for rec in self:
            rec.doc_count = self.env['ir.attachment'].search([('res_model', '=', 'project.task'), ('res_id', '=', rec.id)], count=True) or 0

    @api.one
    def _compute_fields(self):
        self.manager = True if self._uid in [r.id for r in self.env.ref('project.group_project_manager').users] else False
        admins = self.env.ref('kro.group_adm_bp').users
        self.admin = True if self._uid in [r.id for r in admins] else False
        if self.manager:
            self.executor = True
            self.predicator = True
            self.approver = True
            self.planner = True
        if self._uid == self.user_id.id:
            self.planner = True
        if self._uid == self.user_executor_id.id or self.planner:
            self.executor = True
        if self._uid == self.user_predicator_id.id or self.planner:
            self.predicator = True
        if self._uid == self.user_approver_id.id or self.planner:
            self.approver = True

    @api.model
    def default_get(self, fields):
        res = super(Task, self).default_get(fields)
        res['manager'] = True
        res['admin'] = True
        res['planner'] = True
        res['executor'] = True
        res['predicator'] = True
        res['approver'] = True
        return res

    @api.one
    @api.depends('plan_time_ex', 'plan_time_pr', 'plan_time_ap', 'timesheet_ids')
    def _time_count(self):
        self.planned_hours = self.plan_time_ex+self.plan_time_pr+self.plan_time_ap
        time_finished = sum([r.unit_amount for r in self.timesheet_ids])
        if self.planned_hours:
            self.progress = round(min(100.0 * time_finished / self.planned_hours, 99.99), 2)
        if str(self.progress) == '99.99' and self.state == 'finished':
            self.progress = 100.0

    @api.model
    def action_move_time(self, active_id):
        task = self.env['project.task'].browse(active_id)
        start = datetime.datetime.strptime(task.date_start, '%Y-%m-%d')
        end = datetime.datetime.strptime(task.date_end, '%Y-%m-%d')
        for dep in task.dependent_ids:
            r_start = datetime.datetime.strptime(dep.date_start, '%Y-%m-%d')
            r_end = datetime.datetime.strptime(dep.date_end, '%Y-%m-%d')
            r_diff = r_end - r_start
            if r_start < end:
                dep.date_start = task.date_end
                dep.date_end = end + r_diff
            if r_start > end:
                dep.date_start = task.date_end
                dep.date_end = end + r_diff
        for base in task.depend_on_ids:
            r_end = datetime.datetime.strptime(base.date_end, '%Y-%m-%d')
            if r_end > start:
                task.date_start = base.date_end

    @api.model
    def attachment_tree_view(self, active_id):
        task = self.env['project.task'].browse(active_id)
        domain = [('res_model', '=', 'project.task'), ('res_id', '=', task.id)]
        res_id = task.id
        return {
            'name': _('Attachments'),
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                        Documents are attached to the tasks and issues of your project.</p><p>
                        Send messages or log internal notes with attachments to link
                        documents to your project.
                    </p>'''),
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (self._name, res_id)
        }

    @api.one
    @api.depends('date_end_ap', 'date_end_pr')
    def _set_date_end(self):
        end_date_ap = int(self.date_end_ap.replace('-', '')) if self.date_end_ap else 0
        end_date_pr = int(self.date_end_pr.replace('-', '')) if self.date_end_pr else 0
        if end_date_ap >= end_date_pr:
            self.date_end = self.date_end_ap
        elif end_date_ap <= end_date_pr:
            self.date_end = self.date_end_pr

    @api.model
    def create(self, vals):
        if vals['job_id']:
            job = self.env['kro.job'].browse(vals['job_id'])
            vals['private'] = job.private
        subs = []
        vals['user_id'] = self._uid  # для копирования
        user = self.env['res.users'].browse(vals['user_id'])
        if vals.get('user_executor_id', False):
            executor = self.env['res.users'].browse(vals['user_executor_id'])
            if executor != user:
                subs += self.env['mail.followers']._add_follower_command(self._name, [], {executor.partner_id.id: None}, {}, force=True)[0]
        if vals.get('user_approver_id', False):
            approver = self.env['res.users'].browse(vals['user_approver_id'])
            if approver != user:
                subs += self.env['mail.followers']._add_follower_command(self._name, [], {approver.partner_id.id: None}, {}, force=True)[0]
        if vals.get('user_predicator_id', False):
            predicator = self.env['res.users'].browse(vals['user_predicator_id'])
            if predicator != user:
                subs += self.env['mail.followers']._add_follower_command(self._name, [], {predicator.partner_id.id: None}, {}, force=True)[0]
        unique_subs = make_unique(subs)
        if len(subs):
            vals['message_follower_ids'] = unique_subs
            partner_ids = []
            for partner in vals['message_follower_ids']:
                partner_ids.append((4, partner[2]['partner_id']))
            if len(partner_ids):
                vals['partner_ids'] = partner_ids
        res = super(Task, self).create(vals)
        # res.with_context({'mail_post_autofollow': True}).message_post(body='Новая задача', subject='Тема', message_type='notification', subtype='mail.mt_comment', partner_ids=partner_ids)
        return res

    @api.model
    def _store_history(self, ids):
        return True

    def _notification_get_recipient_groups(self, cr, uid, ids, message, recipients, context=None):
        res = super(Task, self)._notification_get_recipient_groups(cr, uid, ids, message, recipients, context=context)
        take_action = self._notification_link_helper(cr, uid, ids, 'assign', context=context)
        new_action_id = self.pool['ir.model.data'].xmlid_to_res_id(cr, uid, 'kro.kro_actions_view_taskss')
        new_action = self._notification_link_helper(cr, uid, ids, 'new', context=context, action_id=new_action_id)
        task_record = self.browse(cr, uid, ids[0], context=context)
        actions = []
        if not task_record.user_id:
            actions.append({'url': take_action, 'title': _('I take it')})
        else:
            actions.append({'url': new_action, 'title': _('Новое задание')})
        res['group_project_user'] = {
            'actions': actions
        }
        return res

    @api.multi
    def write(self, vals):
        if len(self) == 1:
            if vals.get('state') and vals['state'] != self.state:
                current_user = self.env['res.users'].browse(self.env.uid)
                # moment = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
                moment = datetime.datetime.now(pytz.timezone(self.env.context.get('tz') or 'UTC')).strftime('%Y-%m-%d %H:%M:%S')
                vals['state_history'] = (self.state_history or '') + "%s\t%s\t%s\t%s\n" % (moment, vals['state'], current_user.name, self.env.uid)
        res = super(Task, self).write(vals=vals)
        return res


class BlockingUser(models.Model):
    _name = 'res.users.blocking'

    name = fields.Char(u"Имя")
    answered = fields.Boolean(u"Ответил", default=True)
    answer_date = fields.Datetime(u"Дата Ответа")
    task_id = fields.Many2one('project.task', u"Задание")
    user_id = fields.Many2one('res.users', u"Отвечающий")
    set_by_id = fields.Many2one('res.users', u"Спросил")
    message_id = fields.Many2one('mail.message', u"Сообщение")
    body = fields.Html(related="message_id.body", string=u"Сообщение")

    @api.onchange("answered")
    def onchange_answered(self):
        if self.answered:
            self.answer_date = datetime.datetime.now()
        else:
            self.answer_date = False


def make_unique(original_list):
    if not len(original_list):
        return []
    unique_list = []
    [unique_list.append(obj) for obj in original_list if obj not in unique_list]
    return unique_list