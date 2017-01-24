#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

from scription import *
import openerp
import openerp.osv
from openerp.exceptions import ERPError
from openerp.tools import config
from openerp.tests import common
import time
import unittest2

@Script(
        conf=Spec('configuration file to use', OPTION, remove=True),
        tests=Spec('tests to run', OPTION),
        )
def main(conf, *tests):
    config.parse_config(['--conf', conf])
    # inject the configure values back in to openerp.common
    common.ADDONS_PATH = config['addons_path']
    common.PORT = config['xmlrpc_port']
    common.DB = config['db_name']
    common.HOST = '127.0.0.1'
    common.ADMIN_USER = 'admin'
    common.ADMIN_USER_ID = openerp.SUPERUSER_ID
    common.ADMIN_PASSWORD = config['admin_passwd']


@Command()
@Alias('test-fnx-hd.py')
def test_fnx_hd():
    unittest2.main()


class TestFnxHelpDesk(common.TransactionCase):

    def setUp(self):
        """*****setUp*****"""
        print('\n--== setting up ==--')
        super(TestFnxHelpDesk, self).setUp()
        cr, uid, registry = self.cr, self.uid, self.registry
        context = {'mail_track_initial':True}
        res_partner = registry('res.partner')
        res_users = registry('res.users')
        res_groups = registry('res.groups')
        help_desk = registry('fnx.help_desk')
        ir_model_data = registry('ir.model.data')
        mail_message = registry('mail.message')

        triage_group_id = ir_model_data.browse(
                cr, uid,
                [('module','=','fnx_hd'),('model','=','res.groups'),('name','=','fnx_help_desk_triage')],
                )[0].res_id
        inhouse_group_id = ir_model_data.browse(
                cr, uid,
                [('module','=','fnx_hd'),('model','=','res.groups'),('name','=','fnx_help_desk_inhouse')],
                )[0].res_id
        evs_group_id = ir_model_data.browse(
                cr, uid,
                [('module','=','fnx_hd'),('model','=','res.groups'),('name','=','fnx_help_desk_evs')],
                )[0].res_id

        user_id = res_users.create(
                cr, uid,
                {'name':'FnxHD Demo User', 'login':'fnxhd_demo'},
                )
        user = res_users.browse(cr, uid, user_id)

        triage_user_id = res_users.create(
                cr, uid,
                {'name':'FnxHD Demo Triage User', 'login':'fnxhd_demo_triage', 'groups_id':[(4, triage_group_id)]},
                )
        triage_user = res_users.browse(cr, uid, triage_user_id)

        inhouse_user_id = res_users.create(
                cr, uid,
                {'name':'FnxHD Demo In-House User', 'login':'fnxhd_demo_inhouse', 'groups_id':[(4, inhouse_group_id)]},
                )
        inhouse_user = res_users.browse(cr, uid, inhouse_user_id)

        evs_user_id = res_users.create(
                cr, uid,
                {'name':'FnxHD Demo EvS User', 'login':'fnxhd_demo_evs', 'groups_id':[(4, evs_group_id)]},
                )
        evs_user = res_users.browse(cr, uid, evs_user_id)

        triage_group_partner_ids = [
                u.partner_id.id for u in
                res_groups.browse(cr, uid, triage_group_id).users
                ]
        inhouse_group_partner_ids = [
                u.partner_id.id for u in
                res_groups.browse(cr, uid, inhouse_group_id).users
                ]
        evs_group_partner_ids = [
                u.partner_id.id for u in
                res_groups.browse(cr, uid, evs_group_id).users
                ]
        # inject locals into self
        for k, v in locals().items():
            setattr(self, k, v)

    def tearDown(self):
        print('--== tearing down ==--\n')
        super(TestFnxHelpDesk, self).tearDown()

    def _build_error_msg(self, msg, should_be, actual):
        if not isinstance(should_be, (tuple, list)):
            should_be = [should_be]
        if not isinstance(actual, (tuple, list)):
            actual = [actual]
        if not should_be:
            pass
        elif isinstance(should_be[0], (int, long)):
            should_be = sorted([p.name for p in self.res_partner.browse(self.cr, 1, should_be)])
        elif should_be[0]._table._name == 'res.partner':
            should_be = sorted([p.name for p in should_be])
        elif should_be[0]._table._name == 'res.users':
            should_be = sorted([u.partner_id.name for u in should_be])
        else:
            raise ValueError('unknown record type for "should_be": %s' % should_be[0]._table._name)
        if not actual:
            pass
        elif isinstance(actual[0], (int, long)):
            actual = sorted([p.name for p in self.res_partner.browse(self.cr, 1, actual)])
        elif actual[0]._table._name == 'res.partner':
            actual = sorted([p.name for p in actual])
        elif actual[0]._table._name == 'res.users':
            actual = sorted([u.partner_id.name for u in actual])
        else:
            raise ValueError('unknown record type for "actual": %s' % actual[0]._table._name)
        return msg % (should_be, actual)

    def check_followers(self, issue, should_be):
        error_msg = self._build_error_msg(
                'followers:\n  should be -> %s\n  actual -> %s',
                issue.message_follower_ids,
                should_be,
                )
        self.assertEqual(
                set(issue.message_follower_ids),
                set(should_be),
                error_msg,
                )

    def check_notified(self, issue_id, should_be_notified_ids, num_messages):
        time.sleep(1)
        cr, uid= self.cr, self.uid
        if isinstance(should_be_notified_ids, (int, long)):
            should_be_notified_ids = [should_be_notified_ids]
        issue = self.help_desk.browse(cr, 1, issue_id)
        # should_be_notified_ids.extend([p.id for p in issue.message_follower_ids])
        should_be_notified_ids.append(issue.reported_by.partner_id.id)
        if issue.assigned_to:
            should_be_notified_ids.append(issue.assigned_to.partner_id.id)
        should_be_notified_ids = list(set(should_be_notified_ids))
        messages = self.mail_message.browse(cr, uid, [('model','=','fnx.help_desk'),('res_id','=',issue_id)])
        self.assertEqual(len(messages), num_messages, 'expected %d messages, got %d' % (num_messages, len(messages)))
        messages.sort(key=lambda m: m.date)
        message = messages[-1]
        actual_notified_ids = [n.partner_id.id for n in message.notification_ids]
        self.assertEqual(set(should_be_notified_ids), set(actual_notified_ids),
                self._build_error_msg(
                    'discrepency:\nshould be notified -> %s\nactually notified -> %s',
                    should_be_notified_ids,
                    actual_notified_ids,
                    )
                )
        return issue

    def test_simple_create(self):
        """Triage users should be notified"""
        cr, uid, context = self.cr, self.uid, self.context
        issue_id = self.help_desk.create(
            cr, uid,
            dict(
                name='test of the fnx help desk system',
                description='required field to hold in excruciating detail all the particulars',
                reported_by=self.user_id,
                ),
            context=context,
            )
        issue = self.check_notified(issue_id, [self.user.partner_id.id] + self.triage_group_partner_ids, 1)
        self.check_followers(issue, [self.user.partner_id])
        return issue_id

    def test_simple_create_assign_inhouse_user(self):
        """Triage users should /not/ be notified, in-house user should be."""
        cr, uid, context = self.cr, self.uid, self.context
        self.assertRaises(ERPError, self.help_desk.create,
            cr, uid,
            dict(
                name='test of the fnx help desk system',
                description='required field to hold in excruciating detail all the particulars',
                reported_by=self.user_id,
                assigned_to=self.inhouse_user_id,
                ),
            context=context,
            )

    def test_simple_create_assign_evs_user(self):
        """Triage users should /not/ be notified, evs user should be."""
        cr, uid, context = self.cr, self.uid, self.context
        self.assertRaises(ERPError, self.help_desk.create,
            cr, uid,
            dict(
                name='test of the fnx help desk system',
                description='required field to hold in excruciating detail all the particulars',
                reported_by=self.evs_user_id,
                assigned_to=self.evs_user_id,
                ),
            context=context,
            )

    def test_inhouse_create(self):
        """Triage users should be notified"""
        cr, context = self.cr, self.context
        issue_id = self.help_desk.create(
            cr, self.inhouse_user_id,
            dict(
                name='test of the fnx help desk system',
                description='required field to hold in excruciating detail all the particulars',
                reported_by=self.inhouse_user_id,
                ),
            context=context,
            )
        issue = self.check_notified(issue_id, [self.inhouse_user.partner_id.id] + self.triage_group_partner_ids, 1)
        self.check_followers(issue, [self.inhouse_user.partner_id])
        return issue_id

    def test_inhouse_create_assign_inhouse_user(self):
        """Triage users should /not/ be notified, in-house user should be."""
        cr, context = self.cr, self.context
        issue_id = self.help_desk.create(
            cr, self.inhouse_user_id,
            dict(
                name='test of the fnx help desk system',
                description='required field to hold in excruciating detail all the particulars',
                reported_by=self.inhouse_user_id,
                assigned_to=self.inhouse_user_id,
                ),
            context=context,
            )
        issue = self.check_notified(issue_id, [self.inhouse_user.partner_id.id], 1)
        self.check_followers(issue, [self.inhouse_user.partner_id])
        return issue_id

    def test_inhouse_create_assign_evs_user(self):
        """Triage users should /not/ be notified, evs user should be."""
        cr, context = self.cr, self.context
        self.assertRaises(ERPError, self.help_desk.create,
            cr, self.inhouse_user_id,
            dict(
                name='test of the fnx help desk system',
                description='required field to hold in excruciating detail all the particulars',
                reported_by=self.inhouse_user_id,
                assigned_to=self.evs_user_id,
                ),
            context=context,
            )

    def test_evs_create(self):
        """Triage users should be notified"""
        cr, context = self.cr, self.context
        issue_id = self.help_desk.create(
            cr, self.evs_user_id,
            dict(
                name='test of the fnx help desk system',
                description='required field to hold in excruciating detail all the particulars',
                reported_by=self.evs_user_id,
                ),
            context=context,
            )
        issue = self.check_notified(issue_id, [self.evs_user.partner_id.id] + self.triage_group_partner_ids, 1)
        self.check_followers(issue, [self.evs_user.partner_id])
        return issue_id

    def test_evs_create_assign_inhouse_user(self):
        """Triage users should /not/ be notified, in-house user should be."""
        cr, context = self.cr, self.context
        issue_id = self.help_desk.create(
            cr, self.evs_user_id,
            dict(
                name='test of the fnx help desk system',
                description='required field to hold in excruciating detail all the particulars',
                reported_by=self.evs_user_id,
                assigned_to=self.inhouse_user_id,
                ),
            context=context,
            )
        issue = self.check_notified(issue_id, [self.evs_user.partner_id.id, self.inhouse_user.partner_id.id], 1)
        self.check_followers(issue, [self.evs_user.partner_id, self.inhouse_user.partner_id])
        return issue_id

    def test_evs_create_assign_evs_user(self):
        """Triage users should /not/ be notified, evs user should be."""
        cr, context = self.cr, self.context
        issue_id = self.help_desk.create(
            cr, self.evs_user_id,
            dict(
                name='test of the fnx help desk system',
                description='required field to hold in excruciating detail all the particulars',
                reported_by=self.evs_user_id,
                assigned_to=self.evs_user_id,
                ),
            context=context,
            )
        issue = self.check_notified(issue_id, [self.evs_user.partner_id.id], 1)
        self.check_followers(issue, [self.evs_user.partner_id])
        return issue_id

    def test_triage_assign_inhouse_group(self):
        cr, context = self.cr, self.context
        issue_id = self.test_simple_create()
        self.help_desk.write(cr, self.triage_user_id, [issue_id], {'state':'in_house'}, context=context)
        issue = self.check_notified(issue_id, self.inhouse_group_partner_ids, 2)
        self.check_followers(issue, [self.user.partner_id])

    def test_triage_assign_evs_group(self):
        cr, context = self.cr, self.context
        issue_id = self.test_simple_create()
        self.help_desk.write(cr, self.triage_user_id, [issue_id], {'state':'evs'}, context=context)
        issue = self.check_notified(issue_id, self.evs_group_partner_ids, 2)
        self.check_followers(issue, [self.user.partner_id])

    def test_user_assign_inhouse_group(self):
        cr, context = self.cr, self.context
        issue_id = self.test_simple_create()
        self.assertRaises(ERPError, self.help_desk.write, cr, self.user_id, [issue_id], {'state':'evs'}, context=context)

    def test_user_assign_evs_group(self):
        cr, context = self.cr, self.context
        issue_id = self.test_simple_create()
        self.assertRaises(ERPError, self.help_desk.write, cr, self.user_id, [issue_id], {'state':'evs'}, context=context)

Main()
