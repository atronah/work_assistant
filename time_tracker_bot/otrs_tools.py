async def get_otrs_client(endpoint, username, password, webservice_name = 'GenericTicketConnectorSOAP'):
    from otrs.ticket.template import GenericTicketConnectorSOAP
    from otrs.client import GenericInterfaceClient

    if not endpoint:
        raise Exception('Empty endpoint for OTRS')
    if not username or not password:
        raise Exception('Empty credentials for OTRS')

    otrs_client = GenericInterfaceClient(endpoint, tc=GenericTicketConnectorSOAP(webservice_name))
    otrs_client.tc.SessionCreate(user_login=username, password=password)

    return otrs_client