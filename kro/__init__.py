# -*- coding: utf-8 -*-

from . import controllers
from . import models
from openerp import SUPERUSER_ID


def create_code_equal_to_id(cr):
    """
    With this pre-init-hook we want to avoid error when creating the UNIQUE
    code constraint when the module is installed and before the post-init-hook
    is launched.
    """
    cr.execute('ALTER TABLE kro_aim '
               'ADD COLUMN code character varying;')
    cr.execute('UPDATE kro_aim '
               'SET code = id;')

    cr.execute('ALTER TABLE kro_job '
               'ADD COLUMN code character varying;')
    cr.execute('UPDATE kro_job '
               'SET code = id;')


def assign_old_sequences(cr, registry):
    """
    This post-init-hook will update all existing task assigning them the
    corresponding sequence code.
    """
    sequence_obj = registry['ir.sequence']

    aim_obj = registry['kro.aim']
    aim_ids = aim_obj.search(cr, SUPERUSER_ID, [], order="id")
    for task_id in aim_ids:
        cr.execute('UPDATE kro_aim '
                   'SET code = %s '
                   'WHERE id = %s;',
                   (sequence_obj.next_by_code(
                       cr, SUPERUSER_ID, 'kro.aim'), task_id, ))

    job_obj = registry['kro.job']
    job_ids = job_obj.search(cr, SUPERUSER_ID, [], order="id")
    for task_id in job_ids:
        cr.execute('UPDATE kro_job '
                   'SET code = %s '
                   'WHERE id = %s;',
                   (sequence_obj.next_by_code(
                       cr, SUPERUSER_ID, 'kro.job'), task_id, ))
