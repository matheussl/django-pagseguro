#-*- coding: utf-8 -*-
from django.conf import settings
from django.template.loader import render_to_string

from signals import PagSeguroSignal

import urllib
import time


class PagSeguroItem(object):
    """
    PagseguroItem is used by ShopCart to represent the Item.
    """
    def __init__(self, id, description, amount, quantity, shipping_cost=0, weight=0):
        """
        The id param needs be unique by ShopCart.

        The shipping_cost and weight param its optional.
        """
        self.id = id
        self.description = description
        self.amount = amount
        self.quantity = quantity
        self.shipping_cost = shipping_cost
        self.weight = weight



class ShopCart(object):
    """
    
    """
    def __init__(self, **kwargs):
        """
        Cria o CarrinhoPagSeguro com dados iniciais baseado na documentação oficial
        do PagSeguro.

        A constante settings.PAGSEGURO_EMAIL_COBRANCA deve ser configurada com o email
        usado na sua conta do PagSeguro.
        """
        self.cliente = {}
        self.itens = []
        self.config = {
            'tipo' : 'CP',
            'moeda': 'BRL',
            'encoding': 'UTF-8',
            'email_cobranca': settings.PAGSEGURO_EMAIL_COBRANCA,
            'ref_transacao': '',
        }
        self.config.update(kwargs)


def _req_pagseguro(params):
    """ Faz requisição de validação ao PagSeguro """
    params_encode = urllib.urlencode(params)
    res = urllib.urlopen('https://pagseguro.uol.com.br/Security/NPI/Default.aspx', params_encode)
    retorno = res.read()
    res.close()
    return retorno


def validar_dados(dados):
    """
    No retorno automático do PagSeguro essa funcão é responsável
    por validar os dados + token do PagSeguro e emitir o Sinais para
    as outras aplicações.

    Para mais informações sobre o retorno automático e validação do PagSeguro
    consulte:
        https://pagseguro.uol.com.br/desenvolvedor/retorno_automatico_de_dados.jhtml#rmcl

    Caso os dados não sejam verificados a função retorna False e se
    a constante PAGSEGURO_ERRO_LOG estiver definida com um arquivo de log, as informações
    são gravadas.


    A constante settings.PAGSEGURO_TOKEN deve ser configurada com TOKEN fornecido pelo
    PagSeguro.

    A constante settings.PAGSEGURO_ERRO_LOG é opcional e deve ser um arquivo com permissão de escrita,
    exemplo:
        PAGSEGURO_ERRO_LOG = '/tmp/pagseguro_erro.log'

    """
    params = dados.copy()
    params.update({
        'Comando': 'validar',
        'Token': settings.PAGSEGURO_TOKEN,
    })
    retorno = _req_pagseguro(params)
    if retorno == 'VERIFICADO':
        ps_aviso = PagSeguroSignal(dados)
        ps_aviso.send()
        return True
    else:
        erro_log = getattr(settings, 'PAGSEGURO_ERRO_LOG', '')
        if erro_log:
            f = open(erro_log, 'a') 
            f.write("%s - dados: %s - retorno: %s\n" % (time.ctime(), params, retorno))
            f.close()
        return False
