# -*- coding: utf-8 -*-

import logging

from datetime import timedelta
from markupsafe import Markup

from odoo import api, Command, fields, models, tools, _
from odoo.addons.whatsapp.tools import phone_validation as wa_phone_validation
from odoo.exceptions import ValidationError
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT


_logger = logging.getLogger(__name__)

class DiscussChannel(models.Model):
    """ Support Meta Channels, used for discussion with a specific meta user """
    _inherit = 'discuss.channel'

    channel_type = fields.Selection(
        selection_add=[('facebook', 'Facebook Conversation'),('instagram', 'Instagram Conversation')],
        ondelete={'facebook': 'cascade','instagram': 'cascade'})
    meta_partner_id = fields.Many2one(comodel_name='res.partner', string="Meta Partner", index='btree_not_null')
    meta_social_account_id = fields.Many2one(comodel_name='meta.social.account', string="Meta Social Account")

    # INHERITED COMPUTES

    def _compute_is_chat(self):
        super()._compute_is_chat()
        self.filtered(lambda channel: channel.channel_type in ['facebook', 'instagram']).is_chat = True

    def _compute_group_public_id(self):
        meta_channels = self.filtered(lambda channel: channel.channel_type in ["facebook", "instagram"])
        meta_channels.filtered(lambda channel: not channel.group_public_id).group_public_id = self.env.ref('base.group_user')
        super(DiscussChannel, self - meta_channels)._compute_group_public_id()

    # ------------------------------------------------------------
    # MAILING
    # ------------------------------------------------------------

    def _get_notify_valid_parameters(self):
        if self.channel_type == 'facebook':
            return super()._get_notify_valid_parameters() | {'facebook_inbound_msg_uid'}
        elif self.channel_type == 'instagram':
            return super()._get_notify_valid_parameters() | {'instagram_inbound_msg_uid'}
        return super()._get_notify_valid_parameters()

    def _notify_thread(self, message, msg_vals=False, **kwargs):
        # Meta msg must exist before notify to ensure it's included in notifications.
        if kwargs.get('facebook_inbound_msg_uid') and self.channel_type == 'facebook':
            self.env['facebook.message'].create({
                'mail_message_id': message.id,
                'message_type': 'inbound',
                'msg_uid': kwargs['facebook_inbound_msg_uid'],
                'state': 'received',
                'meta_social_account_id': self.meta_social_account_id.id,
            })
        elif kwargs.get('instagram_inbound_msg_uid') and self.channel_type == 'instagram':
            self.env['instagram.message'].create({
                'mail_message_id': message.id,
                'message_type': 'inbound',
                'msg_uid': kwargs['instagram_inbound_msg_uid'],
                'state': 'received',
                'meta_social_account_id': self.meta_social_account_id.id,
            })
        return super()._notify_thread(message, msg_vals=msg_vals, **kwargs)

    def message_post(self, *args, body='', attachment_ids=None, message_type='notification', parent_id=False, **kwargs):
        valid_parent_id = False
        # --------- Validate parent_id for Facebook / Instagram Replies ---------
        if parent_id and self.meta_partner_id:
            parent_msg = self.env['mail.message'].browse(parent_id)

            # Check Facebook message
            fb_msgs = parent_msg.facebook_message_ids
            if (
                    fb_msgs and len(fb_msgs) == 1 and
                    fb_msgs.message_type == "outbound"
                    # TODO: Check recipient identity (e.g. and fb_msgs.recipient_id == self.meta_partner_id)
            ):
                valid_parent_id = parent_id

            # Check Instagram message
            ig_msgs = parent_msg.instagram_message_ids
            if (
                    ig_msgs and len(ig_msgs) == 1 and
                    ig_msgs.message_type == "outbound"
                    # TODO: Check recipient identity (e.g. and ig_msgs.recipient_id == self.meta_partner_id)
            ):
                valid_parent_id = parent_id

        # --------- Determine platform and dispatch ---------
        if message_type in ['instagram_message', 'instagram_message'] and self.channel_type in ['facebook', 'instagram']:
            messages = self._post_social_message(
                platform_key=self.channel_type,
                inbound_uid_key=f'{self.channel_type}_inbound_msg_uid',
                relation_field=f'{self.channel_type}_message_ids',
                message_model=f'{self.channel_type}.message',
                args=args, body=body, attachment_ids=attachment_ids,
                message_type=message_type, parent_id=parent_id,
                kwargs=kwargs, valid_parent_id=valid_parent_id,
            )
            # only return the non-audio message if there are two, as we don't expect to post two messages
            return messages[0] if isinstance(messages, list) else messages

        # --------- Fallback to default message_post ---------
        message = super().message_post(
            *args, body=body, attachment_ids=attachment_ids,
            message_type=message_type, parent_id=parent_id, **kwargs
        )
        if valid_parent_id:
            message.parent_id = valid_parent_id

        return message

    def _post_social_message(self, platform_key, inbound_uid_key, relation_field, message_model,
                             args, body, attachment_ids, message_type, parent_id, kwargs, valid_parent_id):
        messages = None

        # Split message if attachments contain audio and it's an outbound message
        if not kwargs.get(inbound_uid_key) and attachment_ids and body:
            audio_types = self.env[message_model]._SUPPORTED_ATTACHMENT_TYPE['audio']
            attachment_records = self.env['ir.attachment'].browse(attachment_ids)
            audio_attachments = attachment_records.filtered(lambda x: x.mimetype in audio_types)

            if audio_attachments:
                body_message = super().message_post(
                    *args, message_type=message_type, body=body,
                    attachment_ids=(attachment_records - audio_attachments).ids,
                    parent_id=parent_id, **kwargs,
                )
                audio_message = super().message_post(
                    *args, message_type=message_type,
                    attachment_ids=audio_attachments.ids,
                    parent_id=parent_id, **kwargs,
                )
                messages = body_message + audio_message

        # Fallback: normal message
        if not messages:
            messages = super().message_post(
                *args, body=body, message_type=message_type,
                attachment_ids=attachment_ids, parent_id=parent_id, **kwargs,
            )

        # Ensure messages is always a recordset
        if not isinstance(messages, list):
            messages = messages if messages else self.env['mail.message']

        # Prepare and send social messages
        social_message_vals = []
        for new_msg in messages:
            if not getattr(new_msg, relation_field):
                # TODO: use the platform_key here if needed
                social_message_vals.append({
                    'body': new_msg.body,
                    'mail_message_id': new_msg.id,
                    'message_type': 'outbound',
                    'meta_social_account_id': self.meta_social_account_id.id,
                })

        if social_message_vals:
            self.env[message_model].create(social_message_vals)._send_message()

        if valid_parent_id:
            messages.parent_id = valid_parent_id

        return messages

    # ------------------------------------------------------------
    # CONTROLLERS-
    # ------------------------------------------------------------

    @api.returns('self')
    def _get_whatsapp_channel(self, whatsapp_number, wa_account_id, sender_name=False, create_if_not_found=False, related_message=False):
        """ Creates a whatsapp channel.

        :param str whatsapp_number: whatsapp phone number of the customer. It should
          be formatted according to whatsapp standards, aka {country_code}{national_number}.

        :returns: whatsapp discussion discuss.channel
        """
        # be somewhat defensive with number, as it is used in various flows afterwards
        # notably in 'message_post' for the number, and called by '_process_messages'
        base_number = whatsapp_number if whatsapp_number.startswith('+') else f'+{whatsapp_number}'
        wa_number = base_number.lstrip('+')
        wa_formatted = wa_phone_validation.wa_phone_format(
            self.env.company,
            number=base_number,
            force_format="WHATSAPP",
            raise_exception=False,
        ) or wa_number

        related_record = False
        responsible_partners = self.env['res.partner']
        channel_domain = [
            ('whatsapp_number', '=', wa_formatted),
            ('wa_account_id', '=', wa_account_id.id)
        ]
        if related_message:
            related_record = self.env[related_message.model].browse(related_message.res_id)
            responsible_partners = related_record._whatsapp_get_responsible(
                related_message=related_message,
                related_record=related_record,
                whatsapp_account=wa_account_id,
            ).partner_id

            if 'message_ids' in related_record:
                record_messages = related_record.message_ids
            else:
                record_messages = self.env['mail.message'].search([
                    ('model', '=', related_record._name),
                    ('res_id', '=', related_record.id),
                    ('message_type', '!=', 'user_notification'),
                ])
            channel_domain += [
                ('whatsapp_mail_message_id', 'in', record_messages.ids),
            ]
        channel = self.sudo().search(channel_domain, order='create_date desc', limit=1)
        if responsible_partners:
            channel = channel.filtered(lambda c: all(r in c.channel_member_ids.partner_id for r in responsible_partners))

        partners_to_notify = responsible_partners
        record_name = related_message.record_name
        if not record_name and related_message.res_id:
            record_name = self.env[related_message.model].browse(related_message.res_id).display_name
        if not channel and create_if_not_found:
            channel = self.sudo().with_context(tools.clean_context(self.env.context)).create({
                'name': f"{wa_formatted} ({record_name})" if record_name else wa_formatted,
                'channel_type': 'whatsapp',
                'whatsapp_number': wa_formatted,
                'whatsapp_partner_id': self.env['res.partner']._find_or_create_from_number(wa_formatted, sender_name).id,
                'wa_account_id': wa_account_id.id,
                'whatsapp_mail_message_id': related_message.id if related_message else None,
            })
            partners_to_notify |= channel.whatsapp_partner_id
            if related_message:
                # Add message in channel about the related document
                info = _("Related %(model_name)s: ", model_name=self.env['ir.model']._get(related_message.model).display_name)
                url = Markup('{base_url}/web#model={model}&id={res_id}').format(
                    base_url=self.get_base_url(), model=related_message.model, res_id=related_message.res_id)
                related_record_name = related_message.record_name
                if not related_record_name:
                    related_record_name = self.env[related_message.model].browse(related_message.res_id).display_name
                channel.message_post(
                    body=Markup('<p>{info}<a target="_blank" href="{url}">{related_record_name}</a></p>').format(
                        info=info, url=url, related_record_name=related_record_name),
                    message_type='comment',
                    author_id=self.env.ref('base.partner_root').id,
                    subtype_xmlid='mail.mt_note',
                )
                if hasattr(related_record, 'message_post'):
                    # Add notification in document about the new message and related channel
                    info = _("A new WhatsApp channel is created for this document")
                    url = Markup('{base_url}/web#model=discuss.channel&id={channel_id}').format(
                        base_url=self.get_base_url(), channel_id=channel.id)
                    related_record.message_post(
                        author_id=self.env.ref('base.partner_root').id,
                        body=Markup('<p>{info}<a target="_blank" class="o_whatsapp_channel_redirect"'
                                    'data-oe-id="{channel_id}" href="{url}">{channel_name}</a></p>').format(
                                        info=info, url=url, channel_id=channel.id, channel_name=channel.display_name),
                        message_type='comment',
                        subtype_xmlid='mail.mt_note',
                    )
            if partners_to_notify == channel.whatsapp_partner_id and wa_account_id.notify_user_ids.partner_id:
                partners_to_notify |= wa_account_id.notify_user_ids.partner_id
            channel.channel_member_ids = [Command.clear()] + [Command.create({'partner_id': partner.id}) for partner in partners_to_notify]
            channel._broadcast(partners_to_notify.ids)
        return channel

    def whatsapp_channel_join_and_pin(self):
        """ Adds the current partner as a member of self channel and pins them if not already pinned. """
        self.ensure_one()
        if self.channel_type != 'whatsapp':
            raise ValidationError(_('This join method is not possible for regular channels.'))

        self.check_access_rights('write')
        self.check_access_rule('write')
        current_partner = self.env.user.partner_id
        member = self.channel_member_ids.filtered(lambda m: m.partner_id == current_partner)
        if member:
            if not member.is_pinned:
                member.write({'is_pinned': True})
        else:
            new_member = self.env['discuss.channel.member'].with_context(tools.clean_context(self.env.context)).sudo().create([{
                'partner_id': current_partner.id,
                'channel_id': self.id,
            }])
            message_body = Markup(f'<div class="o_mail_notification">{_("joined the channel")}</div>')
            new_member.channel_id.message_post(body=message_body, message_type="notification", subtype_xmlid="mail.mt_comment")
            self.env['bus.bus']._sendone(self, 'mail.record/insert', {
                'Thread': {
                    'channelMembers': [('ADD', list(new_member._discuss_channel_member_format().values()))],
                    'id': self.id,
                    'memberCount': self.member_count,
                    'model': "discuss.channel",
                }
            })
        return self._channel_info()[0]

    # ------------------------------------------------------------
    # OVERRIDE
    # ------------------------------------------------------------

    def _action_unfollow(self, partner):
        if self.channel_type == 'whatsapp' \
                and ((self.whatsapp_mail_message_id \
                and self.whatsapp_mail_message_id.author_id == partner) \
                or len(self.channel_member_ids) <= 2):
            msg = _("You can't leave this channel. As you are the owner of this WhatsApp channel, you can only delete it.")
            self._send_transient_message(partner, msg)
            return
        super()._action_unfollow(partner)

    def _channel_info(self):
        channel_infos = super()._channel_info()
        channel_infos_dict = {c['id']: c for c in channel_infos}

        for channel in self:
            if channel.channel_type == 'whatsapp':
                channel_infos_dict[channel.id]['whatsapp_channel_valid_until'] = \
                    channel.whatsapp_channel_valid_until.strftime(DEFAULT_SERVER_DATETIME_FORMAT) \
                    if channel.whatsapp_channel_valid_until else False

        return list(channel_infos_dict.values())

    # ------------------------------------------------------------
    # COMMANDS
    # ------------------------------------------------------------

    def execute_command_leave(self, **kwargs):
        if self.channel_type == 'whatsapp':
            self.action_unfollow()
        else:
            super().execute_command_leave(**kwargs)
