odoo.define('kro_subscribe_group.Chatter', function (require) {
"use strict";

var core = require('web.core');
var Chatter = require('mail.Chatter');
var widgets = require('web.form_widgets');

var _t = core._t;

core.form_widget_registry.get('mail_followers').include({
    bind_events: function () {
        var self = this;

        this.$el.on('click', '.o_add_group_follower', function(event) {
            event.preventDefault();
            self.on_invite_group_follower(false);
        });
        this._super.apply(this, arguments);
    },

    on_invite_group_follower: function (channel_only) {
        var self = this;
        var action = {
            type: 'ir.actions.act_window',
            res_model: 'mail.wizard.invite.group',
            view_mode: 'form',
            view_type: 'form',
            views: [[false, 'form']],
            name: _t('Добавить группы пользователей'),
            target: 'new',
            context: {
                'default_res_model': this.view.dataset.model,
                'default_res_id': this.view.datarecord.id,
                'mail_invite_follower_channel_only': channel_only,
            },
        };
        this.do_action(action, {
            on_close: function () {
                self.read_value();
            },
        });
    },

});

});
