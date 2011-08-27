# MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 Free Software Foundation, Inc
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

import cgi

from webob import exc

from mediagoblin import messages, mg_globals
from mediagoblin.util import render_to_response, redirect
from mediagoblin.util import pass_to_ugettext as _

from openid.consumer import consumer
from openid.store import memstore
from openid.extensions import sreg

from openidmongodb import MongoDBStore


openid_store = None


def openid_verify(request):
    request.session['foo'] = 'bar'
    import pdb
    output = ''

    # pdb.set_trace()
    openid_url = request.POST.get('openid_url')

    print openid_url

#    immediate = False
    use_sreg = True

    _consumer = _get_consumer(request)

    try:
        req = _consumer.begin(openid_url)
    except consumer.DiscoveryFailure, exc:
        fetch_error_string = 'Error in discovery: %s' % (
            cgi.escape(str(exc[0])))
        self.render(fetch_error_string,
                    css_class='error',
                    form_contents=openid_url)
    else:
        if req is None:
            msg = 'No OpenID services found for <code>%s</code>' % (
                cgi.escape(openid_url),)

        else:
            # Then, ask the library to begin the authorization.
            # Here we find out the identity server that will verify the
            # user's identity, and get a token that allows us to
            # communicate securely with the identity server.
            if use_sreg:
                sreg_request = sreg.SRegRequest(
                    required=['nickname', 'email'])
                req.addExtension(sreg_request)

            trust_root = u'http://' + request.host
            return_to = trust_root + request.urlgen('mediagoblin.openid.process')
            if req.shouldSendRedirect():
                redirect_url = req.redirectURL(
                    trust_root, return_to, immediate=immediate)
                return redirect(
                    request,
                    redirect_url)
            else:
                form_html = req.htmlMarkup(
                    trust_root, return_to,
                    form_tag_attrs={'id':'openid_message'})

                output += form_html

    output += str(req)

    request.session.save()

    return render_to_response(
        request,
        'mediagoblin/openid/foo.html',
        {'output': output})


def openid_process(request):
    output = ''

    _consumer = _get_consumer(request)

    url = u'http://' + '/'.join([
            request.host,
            request.urlgen(
                'mediagoblin.openid.process')])

    response = _consumer.complete(request.matchdict, url)
    display_identifier = response.getDisplayIdentifier()

    if response.status == consumer.FAILURE:
        output += 'Verification of %s failed: %s' % (
            cgi.escape(display_identifier) if display_identifier else '',
            response.message)
        
    elif response.status == consumer.SUCCESS:
        messages.add_message(
            request,
            messages.SUCCESS,
            _('OpenID authentication successful'))

    else:
        output += 'No success<br />'

    output += str(request.session)

    return render_to_response(
        request,
        'mediagoblin/openid/foo.html',
        {'output': output})

def _get_consumer(request):
    global openid_store

    if not openid_store:
        openid_store = MongoDBStore(
            host=mg_globals.app_config['db_host'],
            port=mg_globals.app_config['db_port'],
            db=mg_globals.app_config['db_name'])

    return consumer.Consumer(request.session, openid_store)
