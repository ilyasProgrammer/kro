# -*- coding: utf-8 -*-
{
    'name': "kro_subscribe_group",
    'description': """kro_subscribe_group""",
    'summary': """kro_subscribe_group""",
    'author': "Ilyas",
    'website': "https://github.com/ilyasProgrammer",
    'category': 'Project',
    'version': '1.0',
    'depends': [
        'kro',
        'mail',
                ],
    'data': [
        'wizard/invite_view.xml',
        'templates.xml'
    ],
    'qweb': [
'static/src/xml/chatter.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
