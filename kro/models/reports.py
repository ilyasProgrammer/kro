# -*- coding: utf-8 -*-

from openerp import models, fields, api, tools


class MarkReport(models.Model):
    # Итог не пересчитывается если применяются фильтры
    _name = "mark.report"
    _auto = False
    current_user_id = fields.Many2one('res.users', string='Ответственный')
    parent_project_id = fields.Char(string='Проект')
    date_end_ex = fields.Char(string='Дата окончания')
    name = fields.Many2one('project.task', string='Задание')
    mark_state = fields.Integer(string='Оценка состояния')
    mark_result = fields.Integer(string='Оценка результата')

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'mark_report')
        cr.execute("""
            create or replace view mark_report as (
                    SELECT a.id, 
                    a.current_user_id as current_user_id,
                    a.date_end_ex as date_end_ex,
                    a.id as name,
                    c.name as parent_project_id,
                    CAST (a.mark_state AS INTEGER) as mark_state,
                    CAST (a.mark_result AS INTEGER) as mark_result
                    FROM project_task  a
                    LEFT JOIN kro_job as b on (a.job_id = b.id)
                    LEFT JOIN kro_aim as c on (b.aim_id = c.id)
                    LEFT JOIN kro_problem as d on (c.problem_id = d.id)
                    union ALL
                    SELECT 1 id, 1 current_user_id,
                    null,
                    null ,
                    'Среднее по оценкам' as parent_project_id,
                    AVG(CAST (a.mark_state AS INTEGER)) as mark_state,
                    AVG(CAST (a.mark_result AS INTEGER)) as mark_result
                    FROM project_task  a
                    GROUP BY 1
            )
        """)
