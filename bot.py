import telebot  # Usado para criar um bot do Telegram.
from telebot.types import  InlineKeyboardMarkup, InlineKeyboardButton  # Permite criar botões no bot do Telegram.
from datetime import datetime  # Trabalham com datas e horários.
import pandas as pd  # Manipula dados em formato de tabela (como planilhas do Excel).
from fpdf import FPDF  # Cria arquivos PDF.
import threading  # Permite executar múltiplas tarefas ao mesmo tempo.
from openpyxl import load_workbook  # Trabalha com arquivos do Excel (.xlsx).
from dotenv import load_dotenv  # Carrega variáveis de ambiente (como senhas armazenadas separadamente).
import os  # Manipula arquivos e variáveis do sistema.
import time # Importa a biblioteca que permite fazer pausas no código
import schedule # Biblioteca para agendar tarefas que serão executadas em intervalos de tempo

load_dotenv()  # Carrega as variáveis de ambiente do arquivo .env

CHAVE_API = os.getenv("TELEGRAM_API_KEY")  # Obtém a chave do bot do Telegram do arquivo .env.
bot = telebot.TeleBot(CHAVE_API)  # Cria um bot do Telegram usando essa chave.

# Dicionário global para armazenar as informações de todas as lojas ao longo do dia
informacoes_diarias = {}

# Lista de lojas autorizadas (número da loja: nome e funcionários)
lojasCadastradas = {
    "1": {"nome": "Loja 1", "Funcionários": ["Fernando", "Fatima"]},
    "2": {"nome": "Loja 4", "Funcionários": ["Rafael", "Renata"]},
    "3": {"nome": "Loja 5", "Funcionários": ["João", "Maria"]},
}
def agendar_tarefas():
    while True:
    #vai repetir o código infinitamente enquanto a condição que é dada for verdadeira, O True é uma condição que sempre é verdadeira, então o código vai rodar para sempre.
        schedule.run_pending() # comando que diz para rodar todas as tarefas que foram agendadas e que já estão no momento certo para serem executadas.
        time.sleep(1) 
        ''' faz com que o programa pause por 1 segundo a cada vez que o laço de repetição roda. Isso é importante porque sem essa pausa,
        o programa ficaria verificando continuamente as tarefas pendentes de maneira muito rápida, o que poderia causar sobrecarga no computador sem necessidade.'''

# Iniciar o agendamento em uma thread separada
tarefa_agendamento = threading.Thread(target=agendar_tarefas)
'''Esta linha cria uma nova thread. Uma thread é como um "mini-programa" que pode rodar em paralelo ao seu programa principal. 
diz ao Python que, quando essa thread for iniciada, ela deve executar a função agendar_tarefas.
Ou seja, o agendamento das tarefas vai rodar em uma thread separada enquanto o restante do programa pode continuar funcionando normalmente.'''
tarefa_agendamento.daemon = True  # Isso garante que a thread seja fechada quando o programa principal for finalizado
tarefa_agendamento.start()

# Dicionário global para armazenar informações dos usuários
usuarios = {}

# Verifica se o usuario_id já existe em usuarios.Se não existir, ela cria um novo registro para esse usuário com informações iniciais: loja, funcionários e ausências.

def get_usuario(usuario_id):
    if usuario_id not in usuarios:
        #Se o usuario_id não existir no dicionário usuarios, o que acontece dentro do if será executado.
        usuarios[usuario_id] = {
            #Aqui, se o usuario_id não for encontrado no dicionário usuarios, vamos adicionar um novo item ao dicionário. 
            "loja": None, # Inicialmente é None, o que significa que o usuário ainda não tem uma loja associada a ele.
            "funcionarios": {},# Inicialmente é um dicionário vazio, que provavelmente será usado para armazenar informações sobre os funcionários relacionados a esse usuário.
            "ausencias": {} # Também é um dicionário vazio, que provavelmente será usado para armazenar informações sobre as ausências de funcionários
        }
    return usuarios[usuario_id] # retorna os dados desse usuário.

# Função para criar o menu principal
def menu_principal():
    markup = InlineKeyboardMarkup() # cria um menu de botões que pode ser mostrado dentro de uma interface de chat 
    markup.add(InlineKeyboardButton("Finalizar", callback_data="finalizar_conversa"))
    # Quando o botão é pressionado, O callback_data serve como uma etiqueta que permite que o bot saiba qual ação foi realizada (neste caso, "finalizar_conversa")
    return markup

# Ajusta a largura das colunas do Excel baseado no conteúdo
def ajustar_largura_colunas(filename):
    # Dentro da função, o primeiro passo é carregar o arquivo Excel usando a função load_workbook
    wb = load_workbook(filename) # é usada para abrir o arquivo Excel especificado por filename
    ws = wb.active # ws vai referenciar a planilha ativa dentro do arquivo Excel
    for col in ws.columns:
    # loop (uma repetição) que vai percorrer todas as colunas da planilha ws. O ws.columns nos dá acesso a todas as colunas da planilha uma por uma.
        max_length = 0 # definimos uma variável chamada max_length que vai armazenar o comprimento máximo do conteúdo, Inicialmente é 0.
        col_letter = col[0].column_letter # pegamos a letra da coluna que representa a identificação dessa coluna na planilha. Col_letter armazenará essa letra.
        for cell in col: # loop para percorrer todas as células dentro da coluna atual
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
                '''atualizamos max_length para armazenar o maior comprimento encontrado entre os valores das células da coluna. 
                Usamos len(str(cell.value)) para contar o número de caracteres do valor da célula (conversão para string, caso o valor seja numérico, por exemplo).'''
        ws.column_dimensions[col_letter].width = max_length + 2
        # altera a largura da coluna. O valor é definido como max_length + 2 para adicionar um pequeno espaço extra e garantir que o conteúdo não fique "apertado".
    wb.save(filename) # salvamos o arquivo

# Função para criar o menu de motivo de ausência com botões inline
def menu_motivo_ausencia(funcionario):
    markup = InlineKeyboardMarkup(row_width=2) # parâmetro row_width=2 indica que os botões serão organizados em duas colunas
    motivos = ["Atraso", "Atestado", "Faltou", "Folga", "Saiu mais cedo", "Fora do horário"]
    # definimos uma lista chamada motivos, que contém as diferentes opções de motivos para uma ausência
    for motivo in motivos:
        # loop para percorrer cada um dos motivos da lista motivos. A variável motivo será uma string que representa cada item na lista.
        markup.add(InlineKeyboardButton(motivo, callback_data=f"motivo_{funcionario}_{motivo}"))
    return markup

# Função para criar o menu de escolha de loja
def menu_escolha_loja():
    markup = InlineKeyboardMarkup(row_width=2)
    for numero, loja in lojasCadastradas.items(): # loop sobre todas as lojas cadastradas
        # lojasCadastradas.items() retorna um par de dados para cada loja, onde numero é o identificador da loja e loja é o dicionário com os detalhes dessa loja (por exemplo, o nome da loja).
        markup.add(InlineKeyboardButton(loja["nome"], callback_data=f"loja_{numero}")) # estamos criando um botão para cada motivo.
        # O callback_data é uma string que pode ser usada para identificar qual botão foi pressionado. Nesse caso,uma combinação do funcionário e do motivo.
    return markup

# Função para criar a lista de funcionários com checkboxes
def menu_funcionarios(usuario_id, loja):
    markup = InlineKeyboardMarkup(row_width=1) # Criamos a estrutura do menu novamente, mas dessa vez com apenas uma coluna de botões   
    funcionarios = loja["Funcionários"] # pegando a lista de funcionários da loja especificada no parâmetro loja
    
    usuario = get_usuario(usuario_id) # buscamos os dados do usuário pelo usuario_id fornecido
    if "funcionarios" not in usuario: 
    # Verificamos se o usuário já tem uma chave chamada "funcionarios". Se não tiver, criamos essa chave e a inicializamos como um dicionário vazio.
        usuario["funcionarios"] = {}

    for funcionario in funcionarios: # loop para percorrer cada um dos funcionários da loja
        if funcionario not in usuario["funcionarios"]: # Se o funcionário ainda não estiver registrado para o usuário
            usuario["funcionarios"][funcionario] = {"presente": False} #criamos  um dicionário para ele, com a chave "presente" inicializada como False.
        if usuario["funcionarios"][funcionario]["presente"]: # verificamos se o funcionário está marcado como presente
            button_text = f"✅ {funcionario}" # Se sim, o texto do botão será "✅" antes do nome do funcionário. 
        else:
            button_text = f"{funcionario}" #caso contrário, apenas o nome será exibido.
        
        markup.add(InlineKeyboardButton(button_text, callback_data=f"presente_{funcionario}"))
        # Botão com o texto determinado (se está presente ou não) e configuramos o callback_data para identificar qual funcionário foi pressionado.
    
    markup.add(InlineKeyboardButton("✅ Enviar Presença", callback_data="enviar_presenca"))
    # botão final chamado "✅ Enviar Presença", que, quando pressionado, enviará a presença dos funcionários registrados.
    
    return markup

# Handler para iniciar a conversa e perguntar pela loja
@bot.message_handler(func=lambda mensagem: not get_usuario(mensagem.chat.id)["loja"]) # O decorador @bot.message_handler define uma função que será chamada sempre que o bot receber uma mensagem
# func verifica se o usuário ainda não selecionou uma loja  
def iniciar_conversa(mensagem):
    bot.send_message(mensagem.chat.id, "Selecione o número da sua loja:", reply_markup=menu_escolha_loja()) # Essa linha envia uma mensagem de volta para o usuário.
    # reply_markup adiciona um menu com botões, que é gerado pela função menu_escolha_loja().

# Handler para registrar a loja escolhida
@bot.callback_query_handler(func=lambda call: call.data.startswith('loja_'))
# decorador define uma função que será chamada quando o bot receber uma interação com um botão que começa com a string 'loja_'.
# função recebe o parâmetro call, que contém os dados da interação do botão (informações sobre a escolha do usuário).
def registrar_loja(call):
    numero_loja = call.data.split("_")[1]
    '''o callback_data do botão contém uma string no formato 'loja_<numero>'. Usamos o método split("_") para separar essa string em uma lista. 
    A segunda parte da lista (índice [1]) é o número da loja que o usuário escolheu.'''
    
    if numero_loja in lojasCadastradas: # Verificamos se o número da loja escolhido stá na lista de lojas cadastradas
        loja = lojasCadastradas[numero_loja] # Se a loja foi encontrada, obtemos os detalhes dessa loja     
        usuario_id = call.message.chat.id # Pegamos o ID do usuário que fez a escolha
        usuario = get_usuario(usuario_id) # Buscamos os dados do usuário 
        usuario["loja"] = numero_loja # registramos a loja escolhida no dicionário do usuário, associando o número da loja a ele.
        markup = menu_funcionarios(usuario_id, loja) # Geramos o menu de funcionários da loja selecionada, utilizando a função menu_funcionarios
        bot.send_message(usuario_id, f"Loja registrada: {loja['nome']}. Marque os funcionários que entraram no seu horário normal de trabalho:\nNão digite nada nessa parte!", reply_markup=markup)
        # Enviamos uma mensagem de volta ao usuário, informando que a loja foi registrada e pedindo para marcar os funcionários
    else:
        bot.send_message(call.message.chat.id, "Loja não encontrada! Tente novamente.") # Essa linha é executada caso o número da loja escolhido não esteja na lista de lojas cadastradas.

# Handler para marcar/desmarcar presença de funcionários
@bot.callback_query_handler(func=lambda call: call.data.startswith('presente_'))
# Essa interação ocorre quando o usuário marca ou desmarca a presença de um funcionário.
def marcar_desmarcar_presenca(call):
    funcionario = call.data.split("_")[1] # # A callback_data tem o formato 'presente_<nome_do_funcionario>', e estamos pegando a parte depois do '_.
    usuario_id = call.message.chat.id
    usuario = get_usuario(usuario_id)
    
    if "loja" not in usuario or not usuario["loja"]: # Verificamos se o usuário já selecionou uma loja. Se não, pedimos para ele selecionar uma loja novamente.
        bot.answer_callback_query(call.id, text="Loja não registrada. Por favor, selecione a loja novamente.")
        return
    
    if funcionario not in usuario["funcionarios"]:
        usuario["funcionarios"][funcionario] = {"presente": False}
        '''Verificamos se o funcionário já está registrado no dicionário de funcionários do usuário. 
        Se não estiver, adicionamos esse funcionário com o status de presença como False.'''
    
    usuario["funcionarios"][funcionario]["presente"] = not usuario["funcionarios"][funcionario]["presente"] 
    # alternamos o status de presença do funcionário. Se ele estava marcado como presente, agora será desmarcado, e vice-versa.

    loja = lojasCadastradas[usuario["loja"]] # Obtemos os detalhes da loja selecionada pelo usuário.
    markup_novo = menu_funcionarios(usuario_id, loja) # gera um novo teclado com os funcionários e seus status atualizados.
    markup_atual = call.message.reply_markup  # Obtemos o teclado que está atualmente na tela 

    # Verifica se o novo teclado é diferente do atual
    if markup_atual and markup_novo.to_json() == markup_atual.to_json(): # Como o Telegram usa objetos de teclado, o .to_json() transforma os objetos em texto JSON, permitindo compará-los diretamente.
        bot.answer_callback_query(call.id, text="Nenhuma alteração feita.")  # Mensagem de feedback
        return
    
    # Atualizando a presença visualmente
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup_novo)
    bot.answer_callback_query(call.id, text=f"{funcionario} presença alternada.")

# Handler para o envio da presença
@bot.callback_query_handler(func=lambda call: call.data == "enviar_presenca")
#Essa função é chamada quando o usuário pressiona o botão "Enviar Presença" no bot.
def enviar_presenca(call):
    usuario_id = call.message.chat.id # obtemos o ID do usuário que apertou o botão.
    loja = get_usuario(usuario_id)["loja"] # A função get_usuario(usuario_id) retorna os dados do usuário, incluindo a loja que ele escolheu.
    funcionarios = lojasCadastradas[loja]["Funcionários"] # Pegamos a lista de funcionários dessa loja a partir do dicionário lojasCadastradas
    ausentes = [] # Criamos uma lista vazia para armazenar os funcionários que não compareceram no horário normal.
    
    for funcionario in funcionarios: # Percorremos todos os funcionários da loja.

        if not get_usuario(usuario_id)["funcionarios"][funcionario]["presente"]: # Se presente = False, not faz o False virar True, e o código ENTRA no if.
            ausentes.append(funcionario) # Se estiverem ausentes, adicionamos na lista ausentes.
    
    if ausentes: # Se houver funcionários ausentes
        for funcionario in ausentes: # percorre cada funcionário na lista ausentes
            bot.send_message(
                call.message.chat.id, # Obtém o ID do chat da pessoa que interagiu com o bot (para enviar a mensagem no chat correto).
                f"{funcionario} não entrou no horário normal de trabalho. Qual o motivo?",
                reply_markup=menu_motivo_ausencia(funcionario)
            )
    else:
        bot.send_message(call.message.chat.id, "Todos entraram no horário normal.",
                         reply_markup=menu_principal())
# Handler para selecionar o motivo da ausência
@bot.callback_query_handler(func=lambda call: call.data.startswith("motivo_"))
# vai rodar essa função quando o usuário clicar em um botão com um callback data que começa com "motivo_".
def motivo_ausencia(call):
    usuario_id = call.message.chat.id # Obtém o ID do chat do usuário
    _, funcionario, motivo = call.data.split("_") # Divide a string motivo_funcionario_atraso em três partes
    # _ → Ignora "motivo" (pois não precisamos dele),

    # Registrar motivo no dicionário
    if "ausencias" not in usuarios[usuario_id]: 
        # Se ainda não houver um espaço para armazenar ausências desse usuário, criamos um novo dicionário vazio {}.
        usuarios[usuario_id]["ausencias"] = {}

    usuarios[usuario_id]["ausencias"][funcionario] = {"motivo": motivo} # Armazena o motivo da ausência do funcionário no dicionário.

    # Processar o motivo com base na escolha
    if motivo == "Atraso":
        mostrar_opcoes_atraso(call, funcionario)
    elif motivo == "Atestado":
        mostrar_opcoes_atestado(call, funcionario)
    elif motivo == "Faltou":
        mostrar_opcoes_faltou(call, funcionario)
    elif motivo == "Folga":
        registrar_folga(call, funcionario)
    elif motivo == "Saiu mais cedo":
        mostrar_opcoes_saiu_mais_cedo(call, funcionario)
    elif motivo == "Fora do horário":
        registrar_fora_do_horario(call, funcionario)

# Função para exibir as opções de atraso
def mostrar_opcoes_atraso(call, funcionario):
    # Cria um menu com botões para o usuário escolher se o atraso foi em horas ou minutos.
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Horas", callback_data=f"atraso_horas_{funcionario}"),
        InlineKeyboardButton("Minutos", callback_data=f"atraso_minutos_{funcionario}")
    )
    bot.send_message(call.message.chat.id, f"Quanto tempo de atraso para {funcionario}?", reply_markup=markup)

# Função para exibir as opções de atestado
def mostrar_opcoes_atestado(call, funcionario):
    # Se o usuário escolheu "Atestado", o bot pergunta quando ele deseja enviar o atestado.
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("Agora", callback_data=f"atestado_agora_{funcionario}"),
        InlineKeyboardButton("Depois", callback_data=f"atestado_depois_{funcionario}"),
        InlineKeyboardButton("Já Enviei", callback_data=f"atestado_ja_{funcionario}")
    )
    bot.send_message(call.message.chat.id, f"Deseja enviar o atestado agora ou depois?", reply_markup=markup)

# Função para exibir as opções de falta
def mostrar_opcoes_faltou(call, funcionario):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("Sim", callback_data=f"ausente_sim_{funcionario}"),
        InlineKeyboardButton("Não", callback_data=f"ausente_nao_{funcionario}")
    )
    bot.send_message(call.message.chat.id, f"A falta de {funcionario} foi acordada previamente?", reply_markup=markup)

# Função para registrar folga
def registrar_folga(call, funcionario):
    bot.send_message(call.message.chat.id, f"A ausência de {funcionario} foi justificada como folga.", reply_markup=menu_principal())

# Função para exibir as opções de "Saiu mais cedo"
def mostrar_opcoes_saiu_mais_cedo(call, funcionario): # Essa função será chamada quando um funcionário tiver saído mais cedo
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Horas", callback_data=f"cedo_horas_{funcionario}"), # Se o usuário quiser registrar a saída em horas.
        InlineKeyboardButton("Minutos", callback_data=f"cedo_minutos_{funcionario}") # Se o usuário quiser registrar a saída em minutos
    )
    bot.send_message(call.message.chat.id, f"Quantos minutos {funcionario} saiu mais cedo?", reply_markup=markup)

# Função para registrar "Fora do horário"
def registrar_fora_do_horario(call, funcionario): # Essa função será usada quando um funcionário esteve fora do horário de trabalho.
    bot.send_message(call.message.chat.id, f"A ausência de {funcionario} foi justificada por estar fora de horário de trabalho", reply_markup=menu_principal())

# Função para registrar tempo de atraso
@bot.callback_query_handler(func=lambda call: call.data.startswith("atraso_"))
def registrar_tempo_atraso(call): # função é acionada quando o usuário escolhe "Atraso" e precisa informar o tempo.
    usuario_id = call.message.chat.id # Pega o ID do usuário que enviou a mensagem
    _, tipo, funcionario = call.data.split("_") # Divide o callback_data em três partes

    if tipo == "horas": # Se o atraso for em horas, o bot pergunta quantas horas
        bot.send_message(usuario_id, f"Quantas horas de atraso para {funcionario}?")
        bot.register_next_step_handler_by_chat_id(usuario_id, registrar_tempo_em_horas_atraso, funcionario) # Assim que o usuário responder, a função registrar_tempo_em_horas_atraso será chamada automaticamente para processar a resposta.
    elif tipo == "minutos": # Se o atraso for em minutos, o bot pergunta quantos minutos
        bot.send_message(usuario_id, f"Quantos minutos de atraso para {funcionario}?")
        bot.register_next_step_handler_by_chat_id(usuario_id, registrar_tempo_em_minutos_atraso, funcionario)
        # bot.register_next_step_handler_by_chat_id - Ela informa ao bot que ele deve esperar a próxima mensagem do usuário e quando essa mensagem chegar, chamar uma função específica

# Função para registrar tempo em horas de atraso
def registrar_tempo_em_horas_atraso(message, funcionario): # Essa função será chamada quando o usuário responder com o tempo de atraso em horas
    usuario_id = message.chat.id
    try: # Tenta converter a resposta do usuário em um número inteiro
        horas = int(message.text) # Se o usuário digitou algo inválido ("duas horas"), o código vai falhar e pular para o bloco except.
        if "tempo_atraso" not in usuarios[usuario_id]["ausencias"][funcionario]: # Verifica se já existe um espaço para armazenar o tempo de atraso no dicionário usuarios
            usuarios[usuario_id]["ausencias"][funcionario]["tempo_atraso"] = {} # Se não existir, cria um espaço para salvar os dados de atraso do funcionário.
        usuarios[usuario_id]["ausencias"][funcionario]["tempo_atraso"]["tempo_atraso_horas"] = horas # Salva o número de horas de atraso no dicionário do funcionário   
        bot.send_message(usuario_id, f"O tempo de atraso de {funcionario} foi de {horas} horas. Qual o motivo do atraso?")
        bot.register_next_step_handler_by_chat_id(usuario_id, registrar_motivo_atraso, funcionario) # Quando o usuário responder com o motivo do atraso, a função registrar_motivo_atraso será chamada.
    except ValueError: # Se a conversão int(message.text) falhar, significa que o usuário digitou algo inválido.
        bot.send_message(usuario_id, "Por favor, insira um número válido de horas.")
        bot.register_next_step_handler_by_chat_id(usuario_id, registrar_tempo_em_horas_atraso, funcionario)

# Função para registrar tempo em minutos de atraso
def registrar_tempo_em_minutos_atraso(message, funcionario): # Essa função será chamada quando o usuário responder com o tempo de atraso em minutos
    usuario_id = message.chat.id
    try:
        minutos = int(message.text)
        if "tempo_atraso" not in usuarios[usuario_id]["ausencias"][funcionario]:
            usuarios[usuario_id]["ausencias"][funcionario]["tempo_atraso"] = {}
        usuarios[usuario_id]["ausencias"][funcionario]["tempo_atraso"]["tempo_atraso_minutos"] = minutos
        bot.send_message(usuario_id, f"O tempo de atraso de {funcionario} foi de {minutos} minutos. Qual o motivo do atraso?")
        bot.register_next_step_handler_by_chat_id(usuario_id, registrar_motivo_atraso, funcionario)
    except ValueError:
        bot.send_message(usuario_id, "Por favor, insira um número válido de minutos.")
        bot.register_next_step_handler_by_chat_id(usuario_id, registrar_tempo_em_minutos_atraso, funcionario)

# Função para registrar motivo do atraso
def registrar_motivo_atraso(message, funcionario): # Essa função salva o motivo do atraso.
    usuario_id = message.chat.id # Pega o ID do usuário que enviou a mensagem
    motivo = message.text[:20]  # Limitar a 20 caracteres
    if len(message.text) > 20: # Se o motivo for muito longo, avisa o usuário que só os primeiros 20 caracteres serão salvos
        bot.send_message(usuario_id, "Motivo muito longo! Apenas os primeiros 20 caracteres serão registrados.")
    if "ausencias" not in usuarios[usuario_id]: # Cria o dicionário de ausências, se ele ainda não existir
        usuarios[usuario_id]["ausencias"] = {}
    if funcionario not in usuarios[usuario_id]["ausencias"]:
        usuarios[usuario_id]["ausencias"][funcionario] = {}
    usuarios[usuario_id]["ausencias"][funcionario]["motivo_atraso"] = motivo # Armazena o motivo do atraso no dicionário do usuário
    bot.send_message(usuario_id, f"Atraso de {funcionario} registrado: {motivo}.", reply_markup=menu_principal())

# Função para tratar a opção de atestado
@bot.callback_query_handler(func=lambda call: call.data.startswith("atestado_")) # O código verifica se o botão clicado começa com "atestado_"
def tratar_atestado(call): # Essa função é chamada automaticamente quando o usuário clica em um botão sobre atestado
    _, opcao, funcionario = call.data.split("_") # Divide a informação recebida do botão em três partes, exemplo atestado_agora_joao
    usuario_id = call.message.chat.id
    if opcao == "agora":
        bot.send_message(usuario_id, f"Por favor, envie o atestado médico de {funcionario} como documento ou imagem.")
        bot.register_next_step_handler_by_chat_id(usuario_id, receber_atestado, funcionario) # Espera a próxima mensagem e chama a função receber_atestado assim que o usuário enviar algo.
    elif opcao == "depois":
        usuarios[usuario_id]["ausencias"][funcionario]["prazo_atestado"] = datetime.now().timestamp() + 86400
        # datetime.now().timestamp() + 86400 significa que o usuário tem 48 horas (86400 segundos) para enviar o documento.
        bot.send_message(usuario_id, "Você tem 48 horas para enviar o atestado. Caso contrário, será contado como falta.", reply_markup=menu_principal())
    elif opcao == "ja": # significa que o atestado já foi enviado antes.
        bot.send_message(usuario_id, f"Atestado já foi enviado previamente.", reply_markup=menu_principal())

# Função para receber o atestado
def receber_atestado(message, funcionario): # significa que o atestado já foi enviado antes.
    usuario_id = message.chat.id
    if message.content_type in ["document", "photo"]: # Verifica se a mensagem contém um documento ou uma imagem.
        usuarios[usuario_id]["ausencias"][funcionario]["atestado"] = True # Marca no dicionário que o funcionário enviou o atestado
        bot.send_message(usuario_id, f"Atestado de {funcionario} recebido com sucesso.", reply_markup=menu_principal())
    else: # Se o usuário enviar algo inválido (exemplo: um texto), o bot avisa e pede novamente.
        bot.send_message(usuario_id, f"Por favor, envie o atestado como documento ou imagem.")
        bot.register_next_step_handler_by_chat_id(usuario_id, receber_atestado, funcionario)

# Função para processar ausência acordada
@bot.callback_query_handler(func=lambda call: call.data.startswith("ausente_")) # O bot monitora cliques em botões que começam com "ausente_"
def ausencia_acordada(call): # Essa função é chamada quando o usuário responde se a ausência foi combinada ou não
    _, resposta, funcionario = call.data.split("_") # Divide a string recebida do botão em três partes, exemplo ausente_sim_joao
    usuario_id = call.message.chat.id
    usuarios[usuario_id]["ausencias"][funcionario]["acordado"] = resposta == "sim" # Registra se a ausência foi combinada (True) ou não combinada (False).

    if resposta == "sim": #  Se a ausência foi combinada, o bot pede uma justificativa.
        bot.send_message(usuario_id, f"A falta do {funcionario} foi acordada, justifique essa ausência.")
    else: #  Se não foi combinada, o bot também pede uma justificativa.
        bot.send_message(usuario_id, f"A falta do {funcionario} não foi acordada, justifique essa ausência.")
    bot.register_next_step_handler_by_chat_id(usuario_id, registrar_justificativa_ausencia, funcionario)
    # O bot espera a próxima resposta e chama registrar_justificativa_ausencia

# Função para registrar justificativa de ausência
def registrar_justificativa_ausencia(message, funcionario): # Essa função é chamada quando o usuário responde com a justificativa.
    usuario_id = message.chat.id
    justificativa = message.text[:20]  # Limitar a 20 caracteres
    usuarios[usuario_id]["ausencias"][funcionario]["justificativa"] = justificativa # Salva a justificativa no dicionário.
    bot.send_message(usuario_id, f"A justificativa de {funcionario} foi registrada: {justificativa}.", reply_markup=menu_principal())

# Função para registrar tempo de "Saiu mais cedo"
@bot.callback_query_handler(func=lambda call: call.data.startswith("cedo_")) # O bot monitora cliques em botões que começam com "cedo_"
def registrar_tempo_saiu_mais_cedo(call): # Essa função é chamada quando o usuário clica no botão de "saiu mais cedo".
    usuario_id = call.message.chat.id
    _, tipo, funcionario = call.data.split("_")
    if tipo == "horas": # se escolheu horas
        bot.send_message(usuario_id, f"Quantas horas {funcionario} saiu mais cedo?")
        bot.register_next_step_handler_by_chat_id(usuario_id, registrar_tempo_em_horas_saiu_mais_cedo, funcionario)
    elif tipo == "minutos": # se escolheu minutos
        bot.send_message(usuario_id, f"Quantos minutos {funcionario} saiu mais cedo?")
        bot.register_next_step_handler_by_chat_id(usuario_id, registrar_tempo_em_minutos_saiu_mais_cedo, funcionario)

# Função para registrar tempo em horas de "Saiu mais cedo"
def registrar_tempo_em_horas_saiu_mais_cedo(message, funcionario): # Essa função é chamada quando o usuário responde com a quantidade de horas
    usuario_id = message.chat.id
    try:
        horas = int(message.text) # Tenta converter a resposta do usuário em um número inteiro.
        if "tempo_saiu_mais_cedo" not in usuarios[usuario_id]["ausencias"][funcionario]:
            usuarios[usuario_id]["ausencias"][funcionario]["tempo_saiu_mais_cedo"] = {}
        usuarios[usuario_id]["ausencias"][funcionario]["tempo_saiu_mais_cedo"]["tempo_saiu_horas"] = horas
        bot.send_message(usuario_id, f"O tempo de {funcionario} que saiu mais cedo foi de {horas} horas.", reply_markup=menu_principal())
    except ValueError:
        bot.send_message(usuario_id, "Por favor, insira um número válido de horas.")
        bot.register_next_step_handler_by_chat_id(usuario_id, registrar_tempo_em_horas_saiu_mais_cedo, funcionario)

# Função para registrar tempo em minutos de "Saiu mais cedo"
def registrar_tempo_em_minutos_saiu_mais_cedo(message, funcionario):
    usuario_id = message.chat.id
    try:
        minutos = int(message.text)
        if "tempo_saiu_mais_cedo" not in usuarios[usuario_id]["ausencias"][funcionario]:
            usuarios[usuario_id]["ausencias"][funcionario]["tempo_saiu_mais_cedo"] = {}
        usuarios[usuario_id]["ausencias"][funcionario]["tempo_saiu_mais_cedo"]["tempo_saiu_minutos"] = minutos
        bot.send_message(usuario_id, f"O tempo de {funcionario} que saiu mais cedo foi de {minutos} minutos.", reply_markup=menu_principal())
    except ValueError:
        bot.send_message(usuario_id, "Por favor, insira um número válido de minutos.")
        bot.register_next_step_handler_by_chat_id(usuario_id, registrar_tempo_em_minutos_saiu_mais_cedo, funcionario)

# Função para registrar a justificativa de "Saiu mais cedo"
def registrar_justificativa_saiu_mais_cedo(message, funcionario): #  Essa função é chamada quando o usuário responde com uma justificativa.
    usuario_id = message.chat.id
    justificativa = message.text[:20]  # Limitar justificativa a 20 caracteres
    usuarios[usuario_id]["ausencias"][funcionario]["justificativa"] = justificativa
    bot.send_message(usuario_id, f"Justificativa de {funcionario}: {justificativa}.", reply_markup=menu_principal())

# Função para excluir arquivos antigos, mas sem excluir arquivos essenciais
def excluir_arquivos_antigos(diretorio, tempo_limite_em_segundos=48*60*60):
    # Itera sobre todos os arquivos no diretório
    for nome_arquivo in os.listdir(diretorio): # Lista todos os arquivos no diretório.
        caminho_arquivo = os.path.join(diretorio, nome_arquivo) # Cria o caminho completo do arquivo.

        # Ignora arquivos essenciais como 'bot.py' e '.env'
        if nome_arquivo in ["bot.py", ".env"]:
            continue

        # Verifica se é um arquivo e se está dentro do limite de tempo
        if os.path.isfile(caminho_arquivo) and (time.time() - os.path.getctime(caminho_arquivo)) > tempo_limite_em_segundos:
            try:
                os.remove(caminho_arquivo)
                print(f"Arquivo {nome_arquivo} excluído.")
            except Exception as e:
                print(f"Erro ao excluir o arquivo {nome_arquivo}: {e}")

# Função para finalizar a conversa e gerar relatórios
@bot.callback_query_handler(func=lambda call: call.data == "finalizar_conversa") 
# Esta função é acionada quando o usuário clica no botão "finalizar_conversa".
def finalizar_conversa(call): # Define a função para finalizar a conversa.
    usuario_id = call.message.chat.id
    nome_loja = lojasCadastradas[usuarios[usuario_id]['loja']]['nome'] # Obtém o nome da loja onde o usuário está registrado
    # Obter message e funcionario armazenados anteriormente
    message = usuarios[usuario_id].get("message")
    funcionario = usuarios[usuario_id].get("funcionario")

    # Verifica se há ausências registradas para o usuário
    if "ausencias" in usuarios[usuario_id] and usuarios[usuario_id]["ausencias"]:
        loja = usuarios[usuario_id]["loja"] # Obtém o código da loja.
        
        # Inicializar a lista de ausências para a loja, se necessário
        if loja not in informacoes_diarias:
            informacoes_diarias[loja] = []
        
        # Adiciona as ausências do funcionário ao relatório diário da loja.
        informacoes_diarias[loja].append(usuarios[usuario_id]["ausencias"])

    # Enviar mensagem finalizando a conversa
    bot.send_message(usuario_id, "Relatório gerado. O relatório foi enviado ao responsável. Mande qualquer mensagem para iniciar uma nova conversa.")
    
    responsavel_ids = [6566910217] # Lista com os IDs dos responsáveis que receberão os relatórios.
    for responsavel_id in responsavel_ids: # Para cada responsável, o bot enviará o relatório.
        relatorio_conteudo = extrair_conteudo_relatorio(usuario_id) # Gera o conteúdo do relatório usando função de mensagem
        # Enviar mensagem finalizando a conversa com o relatório
        bot.send_message(responsavel_id, f"Relatório gerado {nome_loja} de {usuario_id}:\n\n{relatorio_conteudo}")

     # Enviar o atestado, se houver
        if "atestado" in usuarios[usuario_id]["ausencias"].get(funcionario, {}):
            if message.content_type == "document":
                try: # Se o atestado for um documento, envia como arquivo.
                    bot.send_document(responsavel_id, message.document.file_id)
                    bot.send_message(responsavel_id, f"Atestado de {funcionario} enviado.")
                except Exception as e:
                    bot.send_message(responsavel_id, f"Erro ao enviar o atestado como documento: {e}")
            elif message.content_type == "photo": # Se o atestado for uma foto, o bot envia como imagem.
                bot.send_photo(responsavel_id, message.photo[-1].file_id)
                bot.send_message(responsavel_id, f"Atestado de {funcionario} enviado.")
        
     # Após enviar os relatórios para o responsável, excluir os arquivos antigos
    diretorio_relatorios = "./"  # Diretório onde os relatórios são salvos
    excluir_arquivos_antigos(diretorio_relatorios)

# Função para extrair conteúdo do relatório
def extrair_conteudo_relatorio(usuario_id): # Esta função gera o texto do relatório.
    loja = lojasCadastradas[usuarios[usuario_id]['loja']]['nome']
    funcionarios_ausentes = usuarios[usuario_id]["ausencias"]
    # Obtém o nome da loja e os funcionários ausentes.

    conteudo = f"Relatório da Loja: {loja}\n\n" # Cria o cabeçalho do relatório.
    if not usuarios[usuario_id]["ausencias"]: # Se não houver funcionários ausentes, exibe "Todos entraram no horário normal."
       conteudo += f"Todos entraram no horário normal."
    for funcionario, dados in funcionarios_ausentes.items(): # Para cada funcionário ausente, adiciona informações ao relatório.
        conteudo += f"Funcionário: {funcionario}\n" # Adiciona o nome do funcionário.
        
        # Adicionar motivo de ausência, se presente
        if 'motivo' in dados:
            conteudo += f"Motivo: {dados['motivo']}\n"

        # Adicionar tempo de atraso, se presente
        if 'tempo_atraso_horas' in dados.get('tempo_atraso', {}):
            conteudo += f"Tempo de Atraso: {dados['tempo_atraso']['tempo_atraso_horas']} horas\n"
        if 'tempo_atraso_minutos' in dados.get('tempo_atraso', {}):
            conteudo += f"Tempo de Atraso: {dados['tempo_atraso']['tempo_atraso_minutos']} minutos\n"
        
        # Adicionar justificativa de atraso, se presente
        if 'motivo_atraso' in dados:
            conteudo += f"Justificativa de Atraso: {dados['motivo_atraso']}\n"

        # Adicionar tempo de saída mais cedo, se presente
        if 'tempo_saiu_horas' in dados.get('tempo_saiu_mais_cedo', {}):
            conteudo += f"Tempo de Saída Mais Cedo: {dados['tempo_saiu_mais_cedo']['tempo_saiu_horas']} horas\n"
        if 'tempo_saiu_minutos' in dados.get('tempo_saiu_mais_cedo', {}):
            conteudo += f"Tempo de Saída Mais Cedo: {dados['tempo_saiu_mais_cedo']['tempo_saiu_minutos']} minutos\n"
        
        # Adicionar justificativa por sair mais cedo, se presente
        if 'justificativa_saiu_mais_cedo' in dados:
            conteudo += f"Justificativa por sair mais cedo: {dados['justificativa_saiu_mais_cedo']}\n"

        # Verificar e adicionar informações sobre atestado
        if 'atestado' in dados:
            conteudo += "Atestado: Enviado\n"
        if 'prazo_atestado' in dados:
            conteudo += "Atestado: Deve ser enviado em 48 horas\n"

        # Indicar se a ausência foi acordada
        if 'acordado' in dados:
            acordado = "Sim" if dados["acordado"] else "Não"
            conteudo += f"Falta Acordada: {acordado}\n"

        # Adicionar justificativa, se presente
        if 'justificativa' in dados:
            conteudo += f"Justificativa: {dados['justificativa']}\n"
        
        # Linha divisória entre os funcionários
        conteudo += "---------\n"
    
    return conteudo

# Função para enviar atestado, se houver
def enviar_atestado(usuario_id, responsavel_id):
    if "atestado" in usuarios[usuario_id]["ausencias"]: # verifica se tem um atestado
        message = usuarios[usuario_id]["message"] # obtemos a mensagem armazenada do usuário
        try:
            if message.content_type == "document": # Se a mensagem for um documento, enviamos como documento
                bot.send_document(responsavel_id, message.document.file_id)
            elif message.content_type == "photo": # se for uma foto enviamos como uma imagem
                bot.send_photo(responsavel_id, message.photo[-1].file_id)
            bot.send_message(responsavel_id, f"Atestado enviado.")
        except Exception as e:
            bot.send_message(responsavel_id, f"Erro ao enviar o atestado: {e}")

# Função para gerar e enviar relatórios consolidados ao final do dia
def gerar_e_enviar_relatorios_consolidados():
    if not informacoes_diarias: # Se não houver informações, a função apenas exibe um aviso no console
        print("Nenhuma informação para gerar relatórios.")
        return

    # Consolidando os dados de todas as lojas
    dados_consolidados = []
    for loja, ausencias in informacoes_diarias.items(): # informacoes_diarias contém os registros de ausência de cada loja.
        for ausencia in ausencias: # O código percorre todas as lojas e funcionários, juntando tudo em uma lista (dados_consolidados).
            for funcionario, dados in ausencia.items():
                dados_consolidados.append({"Loja": loja, "Funcionário": funcionario, **dados})

    if dados_consolidados: # Se houver dados consolidados, criamos dois arquivos:
        # Gerar e enviar os relatórios consolidados (apenas uma vez)
        gerar_relatorio_pdf_consolidado("Consolidado", dados_consolidados)
        gerar_relatorio_excel_consolidado("Consolidado", dados_consolidados)
        
        # Enviar os relatórios para os responsáveis (apenas uma vez)
        enviar_relatorios_consolidados_para_responsavel("Consolidado", dados_consolidados)
        

    # Resetar o dicionário de informações diárias para o próximo dia
    informacoes_diarias.clear()
    print("Relatórios consolidados enviados e informações diárias resetadas.")

# Função para enviar relatórios consolidados
def enviar_relatorios_consolidados_para_responsavel(loja, dados_consolidados):
    responsavel_ids = [6566910217]  # IDs dos responsáveis
    for responsavel_id in responsavel_ids:
        # Enviar o PDF consolidado
        try:
            with open("relatorio_consolidado_todas_as_lojas.pdf", "rb") as pdf_file:
                bot.send_document(responsavel_id, pdf_file)
        except Exception as e:
            bot.send_message(responsavel_id, f"Erro ao enviar PDF consolidado: {e}")
            print(f"Erro ao enviar PDF: {e}")  # Log de erro

        # Enviar o Excel consolidado
        try:
            with open("relatorio_consolidado_todas_as_lojas.xlsx", "rb") as excel_file:
                bot.send_document(responsavel_id, excel_file)          
        except Exception as e:
            bot.send_message(responsavel_id, f"Erro ao enviar Excel consolidado: {e}")
            print(f"Erro ao enviar Excel: {e}")  # Log de erro

# Função para gerar o relatório em PDF
def gerar_relatorio_pdf_consolidado(nome_relatorio, dados_consolidados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    data_atual = datetime.now().strftime("%H:%M  %d/%m/%Y")
    pdf.cell(200, 10, txt=f"Relatório Consolidado de Ausências - {nome_relatorio} - {data_atual}", ln=True, align='C')

    for dado in dados_consolidados:
        # Dados gerais
        pdf.cell(200, 10, txt=f"Loja: {dado['Loja']}", ln=True)
        pdf.cell(200, 10, txt=f"Funcionário: {dado['Funcionário']}", ln=True)
        pdf.cell(200, 10, txt=f"Motivo: {dado['motivo']}", ln=True)
        
        # Verificando e exibindo tempo de atraso
        if 'tempo_atraso_horas' in dado.get('tempo_atraso', {}):
            pdf.cell(200, 10, txt=f"Tempo de Atraso: {dado['tempo_atraso']['tempo_atraso_horas']} horas", ln=True)
        if 'tempo_atraso_minutos' in dado.get('tempo_atraso', {}):
            pdf.cell(200, 10, txt=f"Tempo de Atraso: {dado['tempo_atraso']['tempo_atraso_minutos']} minutos", ln=True)

        # Justificativa de atraso
        if 'motivo_atraso' in dado:
            pdf.cell(200, 10, txt=f"Justificativa: {dado['motivo_atraso']}", ln=True)

        # Verificando e exibindo tempo de saída mais cedo
        if 'tempo_saiu_horas' in dado.get('tempo_saiu_mais_cedo', {}):
            pdf.cell(200, 10, txt=f"Tempo de Saída Mais Cedo: {dado['tempo_saiu_mais_cedo']['tempo_saiu_horas']} horas", ln=True)
        if 'tempo_saiu_minutos' in dado.get('tempo_saiu_mais_cedo', {}):
            pdf.cell(200, 10, txt=f"Tempo de Saída Mais Cedo: {dado['tempo_saiu_mais_cedo']['tempo_saiu_minutos']} minutos", ln=True)

        # Justificativa por saída mais cedo
        if 'justificativa_saiu_mais_cedo' in dado:
            pdf.cell(200, 10, txt=f"Justificativa por ter saído mais cedo: {dado['justificativa_saiu_mais_cedo']}", ln=True)

        # Informações sobre atestado
        if 'atestado' in dado:
            pdf.cell(200, 10, txt="Atestado: Enviado", ln=True)
        if 'prazo_atestado' in dado:
            pdf.cell(200, 10, txt="Atestado: Deve ser enviado em 24 horas", ln=True)

        # Acordo de falta
        if 'acordado' in dado:
            acordado = "Sim" if dado["acordado"] else "Não"
            pdf.cell(200, 10, txt=f"Falta Acordada: {acordado}", ln=True)

        # Justificativa de falta
        if 'justificativa' in dado:
            pdf.cell(200, 10, txt=f"Justificativa: {dado['justificativa']}", ln=True)

        # Separação visual entre registros de cada funcionário
        pdf.cell(200, 10, txt="----------------------------------------", ln=True)

    # Salvar o PDF com o nome definido
    pdf.output("relatorio_consolidado_todas_as_lojas.pdf")

# Função para gerar o relatório em Excel
def gerar_relatorio_excel_consolidado(nome_relatorio, dados_consolidados):
    data = []
    data_atual = datetime.now().strftime("%H:%M  %d/%m/%Y")

    for dado in dados_consolidados:
        row = {
            "Loja": dado["Loja"],
            "Data": data_atual,
            "Funcionário": dado["Funcionário"],
            "Motivo": dado.get('motivo', None),
            "Motivo do Atraso": dado.get('motivo_atraso', None),
            "Tempo de Atraso (horas)": dado.get('tempo_atraso', {}).get('tempo_atraso_horas', None),
            "Tempo de Atraso (min)": dado.get('tempo_atraso', {}).get('tempo_atraso_minutos', None),
            "Tempo que saiu mais cedo (horas)": dado.get('tempo_saiu_mais_cedo', {}).get('tempo_saiu_horas', None),
            "Tempo que saiu mais cedo (min)": dado.get('tempo_saiu_mais_cedo', {}).get('tempo_saiu_minutos', None),
            "Atestado": "Enviado" if dado.get('atestado', False) else None,
            "Prazo Atestado": "Prazo de 48 horas para o atestado ser entregue" if dado.get('prazo_atestado', False) else None,  # Corrigido nome da chave
            "Falta Acordada": "Sim" if dado.get('acordado', False) else None,  # Ajuste correto
            "Justificativa": dado.get('justificativa', None),
        }
        data.append(row)

    # Criar o DataFrame com todos os dados
    df = pd.DataFrame(data).dropna(axis=1, how='all')
    df.to_excel("relatorio_consolidado_todas_as_lojas.xlsx", index=False)
    ajustar_largura_colunas("relatorio_consolidado_todas_as_lojas.xlsx")


# Agendar a execução da função ao final do dia
schedule.every().day.at("15:20").do(gerar_e_enviar_relatorios_consolidados)

# Reiniciar a conversa quando necessário
@bot.message_handler(func=lambda mensagem: usuarios.get(mensagem.chat.id, {}).get("finalizado", False))
def reiniciar_conversa(mensagem):
    usuario_id = mensagem.chat.id
    usuarios.pop(usuario_id, None)  # Remove dados do usuário
    iniciar_conversa(mensagem)

# Comando /reiniciar chama a função reiniciar_conversa
@bot.message_handler(commands=['reiniciar'])
def retomar_conversa(message):
    reiniciar_conversa(message)

# Inicia o bot
bot.polling()