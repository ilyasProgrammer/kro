# -*- coding: utf-8 -*-
from openerp import http

# class Ttt(http.Controller):
#     @http.route('/ttt/ttt/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ttt/ttt/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ttt.listing', {
#             'root': '/ttt/ttt',
#             'objects': http.request.env['ttt.ttt'].search([]),
#         })

#     @http.route('/ttt/ttt/objects/<model("ttt.ttt"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ttt.object', {
#             'object': obj
#         })