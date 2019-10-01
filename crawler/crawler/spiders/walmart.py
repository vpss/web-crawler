#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec  7 20:49:06 2018

@author: vpss
"""

import scrapy
import re

class WalmartSpider(scrapy.Spider):
    name = "walmart"
    start_urls = ['https://www.walmart.com.br/']
    #Entra em cada categoria do Site da Kabum
    def parse(self, response):
        menu = response.xpath('//dd/a/@href').extract()
        link_quebrado1 = '/departamento/papelaria/5134?utmi_p=wm-desktop/header&utmi_cp=linkheader_todoshopping_papelaria_pos-0'
        link_quebrado2 = '/especial/revelacao-digital?utmi_p=wm-desktop/header&utmi_cp=linkheader_todoshopping_revelacao-digital_pos-0'
        
        menu.remove(link_quebrado1)
        menu.remove(link_quebrado2)
        
        for i, _url in enumerate(menu):
            menu[i] = "https:" + _url
        
        for categoria in menu:
            yield scrapy.Request(
            url = categoria,
            callback = self.parse_sub
            )


    #Entra em cada Subcategoria da categoria que esta executando
    def parse_sub(self, response):
        subcat = response.xpath('//a[@class="left-menu-item"]/@href').extract()
        for i, sub in enumerate(subcat):
            subcat[i] = "https://www.walmart.com.br" + sub
        
        for sub in subcat:
            yield scrapy.Request(
            url = sub,
            callback = self.parse_item
            )
        categoria = response.xpath('//span[@itemprop="title"]/text()').extract()[-1]   
        self.log(categoria)

    #Na página das subcategorias, entra em cada produto da página e realiza a paginação para pegar todos os produtos
    def parse_item(self, response):
        #itens = response.xpath('//div[@class="product-list shelf-multiline"]//li//a/@href').extract()
        itens = response.xpath('//div[@class="product-list shelf-multiline"]/section/ul/li/section/a/@href').extract()

        for i, item in enumerate(itens):
            if(i % 2 != 0):
                itens[i] = []
        itens = [x for x in itens if x]
        
        for i, _url in enumerate(itens):
            itens[i] = "https://www.walmart.com.br" + _url
        for produto in itens:
            yield scrapy.Request(
            url = produto,
            callback = self.parse_details
            )

        #Tratamento de Paginação
        url_atual = response.url
        prox_pagina = response.xpath('//a[@class="btn btn-primary shelf-view-more next"]/@href').extract_first()
        if prox_pagina is None:
            prox_pagina = ""
        
        else:
            nova_url = list()
            for c in url_atual:
                if c == '?':
                    break
                nova_url.append(c)
            
            nova_url = "".join(nova_url)
            nova_url = nova_url + prox_pagina
        
        if prox_pagina:
            yield scrapy.Request(
            url = nova_url,
            callback = self.parse_item
            )

    #Em cada produto extrai as informações para colocar no MongoDB e cada item capturado exibe uma mensagem de log
    def parse_details(self, response):
        
        #URL(string): URL do produto
        #url_produto = "https:" + response.xpath('//head/meta[@property="og:url"]/@content').extract_first()
        url_produto = response.url
        
        #nome(string): Nome do produto
        nome_produto = response.xpath('//h1[@class="product-name"]/text()').extract_first()
        if not nome_produto:
            nome_produto = ""
            
        #descricao: (string) Texto contendo a descrição do produto
        desc = response.xpath('//div[@class="description-content"]//text()').extract()
        if desc:
            for i, string in enumerate(desc):
                desc[i] = re.sub(' +', ' ', string)

        """desc_tipo1 = response.xpath('//div[@class="special-half special-right"]/p/text()').extract()
        desc_tipo2 = response.xpath('//div[@class="special-half special-left"]/p/text()').extract()
        desc_tipo3 = response.xpath('//div[@class="special-left special-one-hundred"]/p/text()').extract()
        desc_tipo4 = response.xpath('//div[@class="special-right special-one-hundred"]/p/text()').extract()
        desc_tipo5 = response.xpath('//div[@class="width50 left margin-left"]/p/text()').extract()
        desc_tipo6 = response.xpath('//div[@class="text"]/p/text()').extract()
        desc_tipo7 = response.xpath('//div[@class="width40 left margin-left"]/p/text()').extract()
        """
        #marca: (string) Marca do produto
        produto_marca = response.xpath('//a[@class="product-brand"]/text()').extract_first()
        if not produto_marca:
            produto_marca = ""

        #categoria: (string) Categoria em que o produto se enquadra
        #categoria = response.xpath('//span[@itemprop="title"]/text()').extract()[-1]   
        categoria = response.xpath('//span[@itemprop="title"]/text()').extract()
        if categoria:
            categoria = categoria[-1]
        else:
            categoria = ""
        
        #navegacao: (string list) Lista de categorias e subcategorias de navegação, indo do mais geral para mais específico
        lista_navega = response.xpath('//ul[@class="breadcrumb clearfix"]/li/a/span[@itemprop="title"]/text()').extract()    

        #nome_vendedor: (string) Nome do vendedor do produto
        vendedor = response.xpath('//div[@class="seller-name"]/p[@class="name"]/text()').extract_first()
        if not vendedor:
            vendedor = ""
    
        #valor: (float) Valor atual do produto
        valor_atual = ""
        valor = response.xpath('//span[@class="int"]/text()').extract_first()
        cent = response.xpath('//span[@class="dec"]/text()').extract_first()
        if valor and cent:
            valor_atual = valor + cent
        elif valor:
            valor_atual = valor
        elif cent:
            valor_atual = cent

        #valor_antigo: (float) Valor do produto sem desconto, se houver
        valor_antigo = response.xpath('//span[@class="product-price-old"]/del/text()').extract_first()
        if not valor_antigo:
            valor_antigo = ""
    

        #imagem_principal: (string) URL da imagem do produto
        img_principal = "https:" + response.xpath('//img[@class="main-picture"]/@src').extract_first()
        if not img_principal:
            img_principal = ""

        #imagens_secundarias: (string list) Lista de URL das imagens secundárias
        img_sec = response.xpath('//img[@class="thumb"]/@src').extract()
        for i, _url in enumerate(img_sec):
            img_sec[i] = "https:" + _url


        #caracteristicas: (dict list) Lista de dicionários contendo as caracteristicas do produto Ex.: [{'name': 'Cor', 'value': 'Preto'}]
        caracteristicas = dict()
        
        for element in response.xpath('//tr'):
            filtro = element.xpath('.//th/text()').extract_first()
            if filtro:
                caracteristicas[filtro] = element.xpath('.//td//text()').extract()
        """
        for teste in response.xpath('//tr'):
            caracteristicas[teste.xpath('.//th/text()').extract_first()] = teste.xpath('.//td//text()').extract()
        
        contemNone = False
        for k in caracteristicas.keys():
            if k is None:
                contemNone = True
        
        if contemNone is True:
            del caracteristicas[None]
        """
        for k,v in caracteristicas.items():
            if '\r\n' in v:
                caracteristicas[k] = [x for x in v if x != '\r\n']


        #dimensoes: (dict) Dicionário com as dimensões do produto Ex.: {'altura': '2,00 cm', 'largura': '40,00 cm', 'peso': '2,59 kg'}
        campo = response.xpath('//dt[@class="dimensions-title"]/text()').extract()
        valor = response.xpath('//dd[@class="dimensions-description"]/text()').extract()
        dimensoes = dict()
        for i, value in enumerate(campo):
            dimensoes[value] = valor[i]


        yield {
            "URL": url_produto,
            "Nome": nome_produto,
            "Descrição": desc,
            "Categoria": categoria,
            "Marca": produto_marca,
            "Navegação": lista_navega,
            "Nome_Vendedor": vendedor,
            "Valor": valor_atual,
            "Valor_Antigo": valor_antigo,
            "Imagem_Principal": img_principal,
            "Imagens_Secudarias": img_sec,
            "Caracteristicas": caracteristicas,
            "Dimensões": dimensoes,
        }
        
        self.log('\n--------------ITEM CAPTURADO--------------\n')