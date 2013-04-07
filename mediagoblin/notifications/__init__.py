# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011, 2012 MediaGoblin contributors.  See AUTHORS.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging

from mediagoblin.db.models import CommentNotification, CommentSubscription
from mediagoblin.notifications.task import send_comment_email
from mediagoblin.notifications.tools import generate_comment_message

_log = logging.getLogger(__name__)

def trigger_notification(comment, media_entry, request):
    '''
    Send out notifications about a new comment.
    '''
    subscriptions = CommentSubscription.query.filter_by(
        media_entry_id=media_entry.id).all()

    for subscription in subscriptions:
        if not subscription.notify:
            continue

        if comment.get_author == subscription.user:
            continue

        cn = CommentNotification(
            user_id=subscription.user_id,
            subject_id=comment.id)

        cn.save()

        if subscription.send_email:
            message = generate_comment_message(
                subscription.user,
                comment,
                media_entry,
                request)

            send_comment_email.apply_async(
                [cn.id, message])


def add_comment_subscription(user, media_entry):
    cn = CommentSubscription.query.filter_by(
        user_id=user.id,
        media_entry_id=media_entry.id).first()
    if cn:
        return

    cn = CommentSubscription(
        user_id=user.id,
        media_entry_id=media_entry.id)
    cn.notify = True
    cn.send_email = True
    cn.save()
