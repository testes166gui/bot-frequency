import telebot # Usado para criar um bot do Telegram.   
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton # Permite criar botões no bot do Telegram.
from datetime import datetime, timedelta # Trabalham com datas e horários.
import pandas as pd # Manipula dados em formato de tabela (como planilhas do Excel).
from fpdf import FPDF # Cria arquivos PDF.
import threading # Permite executar múltiplas tarefas ao mesmo tempo.
from openpyxl import load_workbook # Trabalha com arquivos do Excel (.xlsx).
from dotenv import load_dotenv # Carrega variáveis de ambiente (como senhas armazenadas separadamente).
import os # Manipula arquivos e variáveis do sistema.
import time
import schedule

load_dotenv()  # Carrega as variáveis de ambiente do arquivo .env

CHAVE_API = os.getenv("TELEGRAM_API_KEY") # Obtém a chave do bot do Telegram do arquivo .env.
bot = telebot.TeleBot(CHAVE_API) # Cria um bot do Telegram usando essa chave.

usuarios = {} # Cria um dicionário (estrutura de dados) vazio para armazenar informações de usuários interagindo com o bot.

# Dicionário global para armazenar as informações de todas as lojas ao longo do dia
informacoes_diarias = {}

def agendar_tarefas():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Iniciar o agendamento em uma thread separada
tarefa_agendamento = threading.Thread(target=agendar_tarefas)
tarefa_agendamento.daemon = True  # Isso garante que a thread seja fechada quando o programa principal for finalizado
tarefa_agendamento.start()
# Lista de lojas autorizadas (número da loja: nome e funcionários)
lojasCadastradas = {
    "1": {"nome": "Loja 1", "Funcionários": ["Felipe", "Fatima"]},
    "2": {"nome": "Loja 4", "Funcionários": ["Rafael", "Renata"]},
    "3": {"nome": "Loja 5", "Funcionários": ["João","Maria"]},
}
# Função para criar o menu principal
def menu_principal(): # Cria um menu interativo com um botão chamado "Finalizar".
    markup = InlineKeyboardMarkup() # Cria um teclado inline (botões dentro do chat).
    markup.add(InlineKeyboardButton("Finalizar", callback_data="finalizar_conversa")) # Cria um botão que, ao ser clicado, envia a informação "finalizar_conversa" ao bot.
    return markup # Retorna o teclado criado

# Função para gerar relatório em PDF
def gerar_relatorio_pdf(usuario_id):
    pdf = FPDF() # Inicializa um objeto para criar PDFs.
    pdf.add_page() # Adiciona uma nova página ao PDF.
    pdf.set_font("Arial", size=12) # Define a fonte como Arial, tamanho 12.
    nome_loja = lojasCadastradas[usuarios[usuario_id]['loja']]['nome'] # Obtém o nome da loja que o usuário escolheu.
    data_atual = datetime.now().strftime("%H:%M %d/%m/%Y") # A data e hora atuais formatadas
    pdf.cell(200, 10, txt=f"Relatório de Ausências - {nome_loja} - {data_atual}", ln=True, align='C') # Cria um título no PDF com o nome da loja e a data.
    # o 200 e o 10 significa que essa célula ocupa 200mm de largura e 10mm de altura

    if not usuarios[usuario_id]["ausencias"]: # Se não houver funcionários ausentes, exibe "Todos estão presentes."
       pdf.cell(200, 10, txt="Todos entraram no horário normal.", ln=True, align='C')
    else:
        for funcionario, dados in usuarios[usuario_id]["ausencias"].items():
            # Percorre a lista de ausências e adiciona as informações no PDF.
            pdf.cell(200, 10, txt=f"Funcionário: {funcionario}", ln=True)
            pdf.cell(200, 10, txt=f"Motivo: {dados['motivo']}", ln=True)

            # Adicionar tempo de atraso, considerando se foi em horas ou minutos
            if 'tempo_atraso_horas' in dados.get('tempo_atraso', {}):
                pdf.cell(200, 10, txt=f"Tempo de Atraso: {dados['tempo_atraso']['tempo_atraso_horas']} horas", ln=True)
            if 'tempo_atraso_minutos' in dados.get('tempo_atraso', {}):
                pdf.cell(200, 10, txt=f"Tempo de Atraso: {dados['tempo_atraso']['tempo_atraso_minutos']} minutos", ln=True)
            # Adicionar a justificativa do atraso
            if 'motivo_atraso' in dados:
                pdf.cell(200, 10, txt=f"Justificativa: {dados['motivo_atraso']}", ln=True)

            # Exibir 'Saiu Mais Cedo' caso não esteja vazio
            if 'tempo_saiu_horas' in dados.get('tempo_saiu_mais_cedo', {}):
                pdf.cell(200, 10, txt=f"Tempo de Saída Mais Cedo: {dados['tempo_saiu_mais_cedo']['tempo_saiu_horas']} horas", ln=True)
            if 'tempo_saiu_minutos' in dados.get('tempo_saiu_mais_cedo', {}):
                pdf.cell(200, 10, txt=f"Tempo de Saída Mais Cedo: {dados['tempo_saiu_mais_cedo']['tempo_saiu_minutos']} minutos", ln=True)
            if 'justificativa_saiu_mais_cedo' in dados:
                pdf.cell(200, 10, txt=f"Justificativa por ter saído mais cedo: {dados['justificativa_saiu_mais_cedo']}", ln=True)

            if 'atestado' in dados:
                pdf.cell(200, 10, txt="Atestado: Enviado", ln=True)
            if 'prazo_atestado' in dados:
                pdf.cell(200, 10, txt="Atestado: Deve ser enviado em 24 horas", ln=True)
            if 'acordado' in dados:
                acordado = "Sim" if dados["acordado"] else "Não"
                pdf.cell(200, 10, txt=f"Falta Acordada: {acordado}", ln=True)
            if 'justificativa' in dados:
                pdf.cell(200, 10, txt=f"Justificativa: {dados['justificativa']}", ln=True)
            pdf.cell(200, 10, txt="----------------------------------------", ln=True)

    
    nome_arquivo = nome_loja.replace(" ", "")
    pdf.output(f"relatorio_{nome_arquivo}.pdf")

# Função para gerar relatório em Excel
def gerar_relatorio_excel(usuario_id):
    data = [] # Cria uma lista vazia chamada data, que armazenará os dados a serem adicionados no relatório.

    data_atual = datetime.now().strftime("%H:%M %d/%m/%Y") # Obtendo a data e hora atuais
    nome_loja = lojasCadastradas[usuarios[usuario_id]["loja"]]["nome"]
    # Primeiro, busca no dicionário usuarios a loja em que o usuário está cadastrado.
    # Depois, usa essa informação para encontrar o nome da loja no dicionário lojasCadastradas.

    if not usuarios[usuario_id]["ausencias"]: #  Verifica se não há ausências registradas para os funcionários desse usuário.
        data.append({
            "Loja": nome_loja,
            "Data": data_atual,
            "Mensagem": "Todos entraram no horário normal"
        }) # Adiciona um registro na lista data, indicando que todos chegaram no horário esperado.
    else: #  Caso haja funcionários com ausência, o código percorre (for) cada um deles.
        for funcionario, dados in usuarios[usuario_id]["ausencias"].items():
            row = {
                "Loja": nome_loja,
                "Data": data_atual,
                "Funcionário": funcionario,
                "Motivo": dados.get('motivo', None),
                "Tempo de Atraso (horas)": dados.get('tempo_atraso', {}).get('tempo_atraso_horas', None),
                "Tempo de Atraso (min)": dados.get('tempo_atraso', {}).get('tempo_atraso_minutos', None),
                "Justificativa do Atraso": dados.get('motivo_atraso', None),
                "Tempo de Saída Mais Cedo (horas)": dados.get('tempo_saiu_mais_cedo', {}).get('tempo_saiu_horas', None),
                "Tempo de Saída Mais Cedo (min)": dados.get('tempo_saiu_mais_cedo', {}).get('tempo_saiu_minutos', None),
                "Atestado Enviado": "Sim" if dados.get('atestado', False) else None,
                "Falta Acordada": "Sim" if dados.get('acordado', False) else None,
                "Justificativa da Falta": dados.get('justificativa', None)
            }  
            data.append(row) # Adiciona esse registro à lista data.

    # Criar DataFrame e remover colunas vazias
    df = pd.DataFrame(data).dropna(axis=1, how='all')
    # Remove colunas vazias (dropna(axis=1, how='all') significa "remova as colunas onde todas as células estão vazias").

    # Nome do arquivo
    nome_arquivo = nome_loja.replace(" ", "") # Remove espaços do nome da loja para evitar problemas no nome do arquivo.
    filename = f"relatorio_{nome_arquivo}.xlsx" 

    df.to_excel(filename, index=False) # Salva o DataFrame em um arquivo Excel (.xlsx), sem incluir a coluna de índices (index=False).

    # Ajustar a largura das colunas automaticamente
    ajustar_largura_colunas(filename)

# Ajusta a largura das colunas do Excel baseado no conteúdo
def ajustar_largura_colunas(filename):
    
    wb = load_workbook(filename)
    ws = wb.active
    #  Abre o arquivo Excel e seleciona a planilha ativa.

    for col in ws.columns: # Percorre todas as colunas da planilha.
        max_length = 0 #  Inicia uma variável max_length para medir o tamanho do maior texto da coluna.
        col_letter = col[0].column_letter #obtém a letra da coluna

        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
                # Percorre todas as células da coluna e mede o tamanho do maior conteúdo
        
        ws.column_dimensions[col_letter].width = max_length + 2 # Ajusta a largura da coluna para caber o maior texto mais um pequeno espaço extra.

    wb.save(filename)

# Função para criar o menu de motivo de ausência com botões inline
def menu_motivo_ausencia(funcionario):
    markup = InlineKeyboardMarkup(row_width=2) # Cria um conjunto de botões inline (dentro do chat), com 2 colunas.
    motivos = ["Atraso", "Atestado", "Faltou", "Folga", "Saiu mais cedo", "Fora do horário"] # Lista os motivos disponíveis.

    for motivo in motivos:
        # O callback data inclui o nome do funcionário e o motivo
        markup.add(InlineKeyboardButton(motivo, callback_data=f"motivo_{funcionario}_{motivo}"))
        # Cria um botão para cada motivo.

    return markup

# Função para criar o menu de escolha de loja
def menu_escolha_loja():
    markup = InlineKeyboardMarkup(row_width=2)
    for numero, loja in lojasCadastradas.items():
        markup.add(InlineKeyboardButton(loja["nome"], callback_data=f"loja_{numero}"))
    return markup

# Função para criar a lista de funcionários com checkboxes
def menu_funcionarios(usuario_id, loja):
    markup = InlineKeyboardMarkup(row_width=1) # InlineKeyboardMarkup(row_width=1) define que cada linha do menu terá apenas 1 botão.
    funcionarios = loja["Funcionários"] # Pega a lista de funcionários da loja selecionada.
    
    # Verificar se o usuário tem a chave "funcionarios", caso contrário, inicializar
    if "funcionarios" not in usuarios[usuario_id]:
        usuarios[usuario_id]["funcionarios"] = {}
    
    # Inicializando as informações dos funcionários para o usuário se ainda não foi feito
    for funcionario in funcionarios:
        if funcionario not in usuarios[usuario_id]["funcionarios"]:
            usuarios[usuario_id]["funcionarios"][funcionario] = {"presente": False}
            # Se o funcionário ainda não está no registro do usuário, adiciona ele com a presença marcada como "FALSO" (False).
            # Isso significa que, por padrão, todos os funcionários começam como "ausentes".
        
        # Definindo o texto do botão (com ou sem ✔️)
        if usuarios[usuario_id]["funcionarios"][funcionario]["presente"]:
            button_text = f"✅ {funcionario}"
        else:
            button_text = f"{funcionario}"
        
        markup.add(InlineKeyboardButton(button_text, callback_data=f"presente_{funcionario}"))
    
    # Botão para enviar a presença
    markup.add(InlineKeyboardButton("✅ Enviar Presença", callback_data="enviar_presenca"))
    
    return markup

# Handler para iniciar a conversa e perguntar pela loja
@bot.message_handler(func=lambda mensagem: "loja" not in usuarios.get(mensagem.chat.id, {})) 
# "loja" not in ...: verifica se o usuário ainda não escolheu uma loja, usuarios.get(mensagem.chat.id, {}): pega os dados do usuário ou um dicionário vazio ({}) se ele ainda não tiver interagido.
def iniciar_conversa(mensagem):
    bot.send_message(mensagem.chat.id, "Selecione o número da sua loja:", reply_markup=menu_escolha_loja()) # Usa a função menu_escolha_loja() para gerar os botões.

# Handler para registrar a loja escolhida
@bot.callback_query_handler(func=lambda call: call.data.startswith('loja_'))
def registrar_loja(call):
    numero_loja = call.data.split("_")[1]
    # Extrai o número da loja do callback, Se o callback for "loja_2", numero_loja será "2".

    if numero_loja in lojasCadastradas: #  Verifica se a loja realmente existe.
        loja = lojasCadastradas[numero_loja] # Obtém os dados da loja escolhida.
        usuario_id = call.message.chat.id # Pega o ID do usuário que fez a seleção.
        
        # Inicializando o dicionário para o usuário, caso ainda não tenha sido inicializado
        if usuario_id not in usuarios: # Se o usuário ainda não estiver registrado, cria um novo registro para ele.
            usuarios[usuario_id] = {"loja": numero_loja, "nome_funcionario": None, "ausencias": {}, "funcionarios": {}}
        else:
            # Se já existe o usuário, reinicia as informações de funcionários e presença
            usuarios[usuario_id]["funcionarios"] = {}  # Limpa os funcionários antigos
            usuarios[usuario_id]["ausencias"] = {}     # Limpa as ausências antigas
            usuarios[usuario_id]["loja"] = numero_loja  # Atualiza para a nova loja

        # Criar a lista de funcionários com caixas de seleção
        markup = menu_funcionarios(call.message.chat.id, loja)

        # Confirmar a loja registrada e enviar a lista de funcionários
        bot.send_message(call.message.chat.id, f"Loja registrada: {loja['nome']}. Marque os funcionários que entraram no seu horário normal de trabalho:\nNão digite nada nessa parte!", reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, "Loja não encontrada! Tente novamente.")

# Handler para marcar/desmarcar presença de funcionários
@bot.callback_query_handler(func=lambda call: call.data.startswith('presente_')) # O @bot.callback_query_handler serve para dizer ao bot: "Ei, fique atento! Se alguém clicar em um botão com 'presente_', chame essa função."
def marcar_desmarcar_presenca(call):
    funcionario = call.data.split("_")[1] #  call.data contém um texto como "presente_João", "presente_Maria", etc.
    # O .split("_")[1] separa o texto em partes e pega a segunda, que é o nome do funcionário.
    # Exemplo: "presente_João" → separa em ["presente", "João"] → pegamos "João".

    usuario_id = call.message.chat.id # 

    # Verifica se o usuário já tem informações registradas (loja e funcionários)
    if usuario_id not in usuarios:
        bot.answer_callback_query(call.id, text="Você precisa se registrar primeiro.")
        return

    # Verifica se a loja foi registrada
    if "loja" not in usuarios[usuario_id] or not usuarios[usuario_id]["loja"]:
        bot.answer_callback_query(call.id, text="Loja não registrada. Por favor, selecione a loja novamente.")
        return

    # Inicializar o dicionário de funcionários se necessário
    if "funcionarios" not in usuarios[usuario_id]:
        usuarios[usuario_id]["funcionarios"] = {}

    # Verifica se o funcionário está no dicionário de presença do usuário
    if funcionario not in usuarios[usuario_id]["funcionarios"]:
        usuarios[usuario_id]["funcionarios"][funcionario] = {"presente": False}

    # Alternar o estado de presença
    usuarios[usuario_id]["funcionarios"][funcionario]["presente"] = not usuarios[usuario_id]["funcionarios"][funcionario]["presente"]

    # Atualizando a presença do funcionário
    loja = lojasCadastradas[usuarios[usuario_id]["loja"]]
    markup = menu_funcionarios(usuario_id, loja)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    # Atualizando a presença visualmente
    bot.answer_callback_query(call.id, text=f"{funcionario} presença alternada.")

# Handler para o envio da presença
@bot.callback_query_handler(func=lambda call: call.data == "enviar_presenca")
def enviar_presenca(call):
    usuario_id = call.message.chat.id
    loja = usuarios[usuario_id]["loja"]
    funcionarios = lojasCadastradas[loja]["Funcionários"]

    ausentes = []
    
    # Verificar quais funcionários faltaram
    for funcionario in funcionarios:
        if not usuarios[usuario_id]["funcionarios"][funcionario]["presente"]:
            ausentes.append(funcionario)
    
    # Se houver ausentes, perguntar o motivo
    if ausentes:
        for funcionario in ausentes:
            bot.send_message(
                call.message.chat.id,
                f"{funcionario} não entrou no horário normal de trabalho. Qual o motivo?",
                reply_markup=menu_motivo_ausencia(funcionario)
            )
    
    else:
        bot.send_message(call.message.chat.id, "Todos entraram no horário normal.",
                reply_markup=menu_principal())
    
# Handler para selecionar o motivo da ausência
@bot.callback_query_handler(func=lambda call: call.data.startswith("motivo_"))
def motivo_ausencia(call):
    usuario_id = call.message.chat.id
    _, funcionario, motivo = call.data.split("_")  # Extrair o funcionário e o motivo do callback data

    #Registrar motivo inicial no dicionário do usuário
    if "ausencias" not in usuarios [usuario_id]:
        usuarios[usuario_id]["ausencias"] = {}

    usuarios [usuario_id]["ausencias"][funcionario] = {"motivo":motivo}

    #Processar o motivo com base na escolha
    match motivo:
        case "Atraso":
            markup = InlineKeyboardMarkup(row_width=1)
            markup.add(
                InlineKeyboardButton("Horas", callback_data=f"atraso_horas_{funcionario}"),
                InlineKeyboardButton("Minutos", callback_data=f"atraso_minutos_{funcionario}")
            )
            bot.send_message(
                usuario_id,
                f"Quanto tempo de atraso para {funcionario}?",
                reply_markup=markup
            )
            
        case "Atestado":
            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(
                InlineKeyboardButton("Agora", callback_data=f"atestado_agora_{funcionario}"),
                InlineKeyboardButton("Depois", callback_data=f"atestado_depois_{funcionario}"),
                InlineKeyboardButton("Já Enviei", callback_data=f"atestado_ja_{funcionario}")
            )
            bot.send_message(
                usuario_id,
                f"Deseja enviar o atestado agora ou depois?",
                reply_markup=markup
            )
            
        case "Faltou":
            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(
                InlineKeyboardButton("Sim", callback_data=f"ausente_sim_{funcionario}"),
                InlineKeyboardButton("Não", callback_data=f"ausente_nao_{funcionario}")
            )
            bot.send_message(
                usuario_id,
                f"A falta de {funcionario} foi acordada previamente?",
                reply_markup=markup
            )
        case "Folga":
            bot.send_message(
                usuario_id,
                f"A ausência de {funcionario} foi justificada como folga.",
                reply_markup=menu_principal()
            )
        case "Saiu mais cedo":
            markup = InlineKeyboardMarkup(row_width=1)
            markup.add(
                InlineKeyboardButton("Horas", callback_data=f"cedo_horas_{funcionario}"),
                InlineKeyboardButton("Minutos", callback_data=f"cedo_minutos_{funcionario}")
            )
            bot.send_message(
                usuario_id,
                f"Quantos minutos {funcionario} saiu mais cedo?",
                reply_markup=markup
            )
            
        case "Fora do horário":
            bot.send_message(
                usuario_id,
                f"A ausência de {funcionario} foi justificada por estar fora de horário de trabalho",
                reply_markup=menu_principal()
            )


# Função para registrar tempo de atraso
@bot.callback_query_handler(func=lambda call: call.data.startswith("atraso_"))
def registrar_tempo_atraso(call):
    usuario_id = call.message.chat.id
    _, tipo, funcionario = call.data.split("_")  # Extrair tipo (horas/minutos) e funcionário do callback data
    if tipo == "horas":
        bot.send_message(
            usuario_id,
            f"Quantas horas de atraso para {funcionario}?"
        )
        bot.register_next_step_handler_by_chat_id(
            usuario_id, registrar_tempo_em_horas_atraso, funcionario
        )

    elif tipo == "minutos":
        bot.send_message(
            usuario_id,
            f"Quantos minutos de atraso para {funcionario}?"
        )
        bot.register_next_step_handler_by_chat_id(
            usuario_id, registrar_tempo_em_minutos_atraso, funcionario
        )

# Função para registrar tempo em horas de atraso
def registrar_tempo_em_horas_atraso(message, funcionario):
    usuario_id = message.chat.id
    try:
        horas = int(message.text)
        
        # Inicializar a chave "tempo_atraso" se não existir
        if "tempo_atraso" not in usuarios[usuario_id]["ausencias"][funcionario]:
            usuarios[usuario_id]["ausencias"][funcionario]["tempo_atraso"] = {}
        
        usuarios[usuario_id]["ausencias"][funcionario]["tempo_atraso"]["tempo_atraso_horas"] = horas  # Convertendo para minutos

        # Perguntar pelo motivo do atraso
        bot.send_message(
            usuario_id,
            f"O tempo de atraso de {funcionario} foi de {horas} horas. Qual o motivo do atraso?",
        )
        bot.register_next_step_handler_by_chat_id(
            usuario_id, registrar_motivo_atraso, funcionario
        )
        
    except ValueError:
        bot.send_message(
            usuario_id,
            "Por favor, insira um número válido de horas."
        )
        bot.register_next_step_handler_by_chat_id(
            usuario_id, registrar_tempo_em_horas_atraso, funcionario
        )

def registrar_tempo_em_minutos_atraso(message, funcionario):
    usuario_id = message.chat.id
    try:
        minutos = int(message.text)
        
        # Inicializar a chave "tempo_atraso" se não existir
        if "tempo_atraso" not in usuarios[usuario_id]["ausencias"][funcionario]:
            usuarios[usuario_id]["ausencias"][funcionario]["tempo_atraso"] = {}
        
        usuarios[usuario_id]["ausencias"][funcionario]["tempo_atraso"]["tempo_atraso_minutos"] = minutos

        # Perguntar pelo motivo do atraso
        bot.send_message(
            usuario_id,
            f"O tempo de atraso de {funcionario} foi de {minutos} minutos. Qual o motivo do atraso?",
        )
        bot.register_next_step_handler_by_chat_id(
            usuario_id, registrar_motivo_atraso, funcionario
        )
        
    except ValueError:
        bot.send_message(
            usuario_id,
            "Por favor, insira um número válido de minutos."
        )
        bot.register_next_step_handler_by_chat_id(
            usuario_id, registrar_tempo_em_minutos_atraso, funcionario
        )

# Função para registrar motivo do atraso
def registrar_motivo_atraso(message, funcionario):
    usuario_id = message.chat.id
    motivo = message.text[:20]  # Limitar a 20 caracteres
    
    if len(message.text) > 20:
        bot.send_message(
            usuario_id,
            "Motivo muito longo! Apenas os primeiros 20 caracteres serão registrados."
        )
    
    # Inicializar "ausencias" e o "funcionario" caso não existam
    if "ausencias" not in usuarios[usuario_id]:
        usuarios[usuario_id]["ausencias"] = {}

    if funcionario not in usuarios[usuario_id]["ausencias"]:
        usuarios[usuario_id]["ausencias"][funcionario] = {}

    # Registrar o motivo
    usuarios[usuario_id]["ausencias"][funcionario]["motivo_atraso"] = motivo

    bot.send_message(
        usuario_id,
        f"Atraso de {funcionario} registrado: {motivo}.",
        reply_markup=menu_principal()
    )

#Função para tratar a opção atestado
@bot.callback_query_handler(func=lambda call: call.data.startswith("atestado_"))
def tratar_atestado(call):
    _,opcao,funcionario= call.data.split("_")
    usuario_id = call.message.chat.id

    if opcao == "agora":
        bot.send_message(
            usuario_id,
            f"Por favor, envie o atestado médico de {funcionario} como documento ou imagem."
        )
        bot.register_next_step_handler_by_chat_id(
            usuario_id, receber_atestado, funcionario
        )
    elif opcao == "depois":
        usuarios[usuario_id]["ausencias"][funcionario]["prazo_atestado"] = datetime.now().timestamp() + 86400
        bot.send_message(
            usuario_id,
            "Você tem 48 horas para enviar o atestado. Caso contrário, será contado como falta.",
            reply_markup=menu_principal()
        )
    elif opcao =="ja":
        bot.send_message(
            usuario_id,
            f"Atestado já foi enviado previamente.",
            reply_markup=menu_principal()
        )

#função para receber o atestado
def receber_atestado(message, funcionario):
    usuario_id = message.chat.id

    # Armazenar message e funcionario no dicionário de usuários
    if usuario_id not in usuarios:
        usuarios[usuario_id] = {"ausencias": {}}
    usuarios[usuario_id]["message"] = message
    usuarios[usuario_id]["funcionario"] = funcionario

    #verificar se o arquivo foi enviado
    if message.content_type in ["document", "photo"]:

        # Registrar o atestado no banco de dados (estrutura de dados dos usuários)
        usuarios[usuario_id]["ausencias"][funcionario]["atestado"] = True
        bot.send_message(
            usuario_id,
            f"Atestado de {funcionario} recebido com sucesso.",
            reply_markup=menu_principal()
        )

        
    else:
        bot.send_message(
            usuario_id,
            f"Por favor, envie o atestado como documento ou imagem."
        )
        bot.register_next_step_handler_by_chat_id(
            usuario_id, receber_atestado, funcionario
        )

#handler para processar se ausênciafoi acordada (Sim/Não)
@bot.callback_query_handler(func=lambda call: call.data.startswith("ausente_"))
def ausencia_acordada(call):
    _,resposta, funcionario = call.data.split("_")
    usuario_id = call.message.chat.id

    usuarios[usuario_id]["ausencias"][funcionario]["acordado"] = resposta =="sim"

    
        #f"A ausência de {funcionario} foi marcada como {"acordada" if resposta == "sim" else "não acordada"}."
    if resposta == "sim":
        bot.send_message(
            usuario_id,
            f"A falta do {funcionario} foi acordada, justifique essa ausência"
        )
    else:
        bot.send_message(
            usuario_id,
            f"A falta do {funcionario} não foi acordada, justifique essa ausência"
        )
    f"Por favor, envie uma justificativa (limite: 20 caracteres)."
    

    bot.register_next_step_handler_by_chat_id(
        usuario_id,registrar_justificativa_ausencia,funcionario
    )
    

#Função para registrar justificativa de ausência
def registrar_justificativa_ausencia(message,funcionario):
    usuario_id = message.chat.id
    justificativa = message.text[:20] #Limitar a 20 caracteres
    usuarios[usuario_id]["ausencias"][funcionario]["justificativa"] = justificativa

    bot.send_message(
        usuario_id,
        f"A justificativa de {funcionario} foi registrada: {justificativa}.",
        reply_markup=menu_principal()
    )
# Função para registrar tempo de "Saiu mais cedo"
@bot.callback_query_handler(func=lambda call: call.data.startswith("cedo_"))
def registrar_tempo_saiu_mais_cedo(call):
    usuario_id = call.message.chat.id
    try:
        # Dividir o callback_data
        _, tipo, funcionario = call.data.split("_")
        
        # Verificar se o "funcionario" foi extraído corretamente
        if not funcionario:
            raise ValueError("Funcionário não especificado.")
        
        if tipo == "horas":
            bot.send_message(
                usuario_id,
                f"Quantas horas {funcionario} saiu mais cedo?"
            )
            bot.register_next_step_handler_by_chat_id(
                usuario_id, registrar_tempo_em_horas_saiu_mais_cedo, funcionario
            )

        elif tipo == "minutos":
            bot.send_message(
                usuario_id,
                f"Quantos minutos {funcionario} saiu mais cedo?"
            )
            bot.register_next_step_handler_by_chat_id(
                usuario_id, registrar_tempo_em_minutos_saiu_mais_cedo, funcionario
            )
    
    except ValueError as e:
        bot.send_message(usuario_id, f"Erro: {e}")
        return

# Função para registrar tempo em horas de "Saiu mais cedo"
def registrar_tempo_em_horas_saiu_mais_cedo(message, funcionario):
    usuario_id = message.chat.id
    try:
        horas = int(message.text)
        
        # Inicializar a chave "tempo_saiu_mais_cedo" se não existir
        if "tempo_saiu_mais_cedo" not in usuarios[usuario_id]["ausencias"][funcionario]:
            usuarios[usuario_id]["ausencias"][funcionario]["tempo_saiu_mais_cedo"] = {}

        usuarios[usuario_id]["ausencias"][funcionario]["tempo_saiu_mais_cedo"]["tempo_saiu_horas"] = horas  # Convertendo para minutos
        bot.send_message(
            usuario_id,
            f"O tempo de {funcionario} que saiu mais cedo foi de {horas} horas.",
            reply_markup=menu_principal()
        )
    except ValueError:
        bot.send_message(
            usuario_id,
            "Por favor, insira um número válido de horas."
        )
        bot.register_next_step_handler_by_chat_id(
            usuario_id, registrar_tempo_em_horas_saiu_mais_cedo, funcionario
        )

# Função para registrar tempo em minutos de "Saiu mais cedo"
def registrar_tempo_em_minutos_saiu_mais_cedo(message, funcionario):
    usuario_id = message.chat.id
    try:
        minutos = int(message.text)
        
        # Inicializar a chave "tempo_saiu_mais_cedo" se não existir
        if "tempo_saiu_mais_cedo" not in usuarios[usuario_id]["ausencias"][funcionario]:
            usuarios[usuario_id]["ausencias"][funcionario]["tempo_saiu_mais_cedo"] = {}

        usuarios[usuario_id]["ausencias"][funcionario]["tempo_saiu_mais_cedo"]["tempo_saiu_minutos"] = minutos
        bot.send_message(
            usuario_id,
            f"O tempo de {funcionario} que saiu mais cedo foi de {minutos} minutos.",
            reply_markup=menu_principal()
        )
    except ValueError:
        bot.send_message(
            usuario_id,
            "Por favor, insira um número válido de minutos."
        )
        bot.register_next_step_handler_by_chat_id(
            usuario_id, registrar_tempo_em_minutos_saiu_mais_cedo, funcionario
        )

# Função para registrar a justificativa de "Saiu mais cedo"
def registrar_justificativa_saiu_mais_cedo(message, funcionario):
    usuario_id = message.chat.id
    justificativa = message.text[:100]  # Limitar justificativa a 100 caracteres
    usuarios[usuario_id]["ausencias"][funcionario]["justificativa_saiu_mais_cedo"] = justificativa

    bot.send_message(
        usuario_id,
        f"A saída antecipada de {funcionario} foi registrada com o seguinte motivo: {justificativa}.",
        reply_markup=menu_principal()
    )

# Função para excluir arquivos antigos, com verificação para não excluir arquivos essenciais
def excluir_arquivos_antigos(diretorio, tempo_limite_em_segundos=48*60*60):
    for nome_arquivo in os.listdir(diretorio):
        caminho_arquivo = os.path.join(diretorio, nome_arquivo)

        # Ignorar a exclusão do bot.py
        if nome_arquivo == "bot.py" or nome_arquivo == ".env":
            continue  # Pula o arquivo bot.py

        # Verificar se é um arquivo
        if os.path.isfile(caminho_arquivo):
            # Obter tempo de criação do arquivo
            tempo_criacao = os.path.getctime(caminho_arquivo)

            # Excluir se o arquivo foi criado há mais de 48 horas
            if (time.time() - tempo_criacao) > tempo_limite_em_segundos:
                try:
                    os.remove(caminho_arquivo)
                    print(f"Arquivo {nome_arquivo} excluído.")
                except Exception as e:
                    print(f"Erro ao excluir o arquivo {nome_arquivo}: {e}")

# Handler para finalizar a conversa
@bot.callback_query_handler(func=lambda call: call.data == "finalizar_conversa")
def finalizar_conversa(call):
    usuario_id = call.message.chat.id
    nome_loja = lojasCadastradas[usuarios[usuario_id]['loja']]['nome']
    # Obter message e funcionario armazenados anteriormente
    message = usuarios[usuario_id].get("message")
    funcionario = usuarios[usuario_id].get("funcionario")


    # Verificar se há informações para armazenar
    if "ausencias" in usuarios[usuario_id] and usuarios[usuario_id]["ausencias"]:
        loja = usuarios[usuario_id]["loja"]
        
        # Inicializar a lista de ausências para a loja, se necessário
        if loja not in informacoes_diarias:
            informacoes_diarias[loja] = []
        
        # Adicionar as ausências atuais ao dicionário global
        informacoes_diarias[loja].append(usuarios[usuario_id]["ausencias"])

    # Enviar mensagem finalizando a conversa
    bot.send_message(usuario_id, "Relatório gerado. O relatório foi enviado ao responsável. Mande qualquer mensagem para iniciar uma nova conversa.")
    
    responsavel_ids = [6566910217]
    for responsavel_id in responsavel_ids:
        # Gerar o conteúdo do relatório
        relatorio_conteudo = extrair_conteudo_relatorio(usuario_id)
        # Enviar mensagem finalizando a conversa com o relatório
        bot.send_message(responsavel_id, f"Relatório gerado {nome_loja}:\n\n{relatorio_conteudo}")

     # Enviar o atestado, se houver
        if "atestado" in usuarios[usuario_id]["ausencias"].get(funcionario, {}):
            if message.content_type == "document":
                try:
                    bot.send_document(responsavel_id, message.document.file_id)
                    bot.send_message(responsavel_id, f"Atestado de {funcionario} enviado.")
                except Exception as e:
                    bot.send_message(responsavel_id, f"Erro ao enviar o atestado como documento: {e}")
            elif message.content_type == "photo":
                bot.send_photo(responsavel_id, message.photo[-1].file_id)
                bot.send_message(responsavel_id, f"Atestado de {funcionario} enviado.")
        else:
            bot.send_message(responsavel_id, f"Relatórios enviados de {usuario_id}.")
     # Após enviar os relatórios para o responsável, excluir os arquivos antigos
    diretorio_relatorios = "./"  # Diretório onde os relatórios são salvos
    excluir_arquivos_antigos(diretorio_relatorios)

# Função para enviar relatórios para o responsável
def enviar_relatorio_responsavel(responsavel_id, usuario_id, message, funcionario):
    # Obter nome da loja
    nome_loja = lojasCadastradas[usuarios[usuario_id]['loja']]['nome']
    # Enviar relatórios para o responsável
   # gerar_relatorio_pdf(usuario_id)
    #gerar_relatorio_excel(usuario_id)

    # Extrair o conteúdo do relatório para enviar como mensagem
    relatorio_conteudo = extrair_conteudo_relatorio(usuario_id)  # Função para extrair o conteúdo

    # Enviar o conteúdo extraído como mensagem
    bot.send_message(responsavel_id, f"Conteúdo do Relatório para {nome_loja}:\n\n{relatorio_conteudo}")

    # Enviar o PDF e o Excel para o responsável
    bot.send_message(responsavel_id, f"Relatórios gerados pelo usuário {usuario_id}:")
    
    '''# Enviar arquivo PDF
    try:
        nome_arquivo = nome_loja.replace(" ", "")
        with open(f"relatorio_{nome_arquivo}.pdf", "rb") as pdf_file:
            bot.send_document(responsavel_id, pdf_file)
    except Exception as e:
        bot.send_message(responsavel_id, f"Erro ao enviar PDF para {usuario_id}: {e}")

    # Enviar arquivo Excel
    try:
        nome_arquivo = nome_loja.replace(" ", "")
        with open(f"relatorio_{nome_arquivo}.xlsx", "rb") as excel_file:
            bot.send_document(responsavel_id, excel_file)
    except Exception as e:
        bot.send_message(responsavel_id, f"Erro ao enviar Excel para {usuario_id}: {e}")
'''
    # Verificar se o atestado foi enviado e encaminhá-lo
    if "atestado" in usuarios[usuario_id]["ausencias"].get(funcionario, {}):
          # Se houver atestado, enviar o documento ou foto
        if message.content_type == "document":
            try:
                # Enviar o documento com o file_id
                bot.send_document(responsavel_id, message.document.file_id)
                bot.send_message(responsavel_id, f"  atestado enviado para o usuário {responsavel_id}.")
            except Exception as e:
                bot.send_message(responsavel_id, f"Erro ao enviar o atestado como documento: {e}")
        elif message.content_type == "photo":
            bot.send_message(responsavel_id, f"Atestado de {funcionario}:")
            bot.send_photo(responsavel_id, message.photo[-1].file_id)
            bot.send_message(responsavel_id, f"Relatórios e atestado enviados para o usuário {responsavel_id}.")
    else:
        # Se não houver atestado, apenas envie a mensagem de conclusão
        bot.send_message(responsavel_id, f"Relatórios enviados para o usuário {responsavel_id}.")

# Função para extrair o conteúdo do relatório gerado para a mensagem
def extrair_conteudo_relatorio(usuario_id):
    # Obter nome da loja
    loja = lojasCadastradas[usuarios[usuario_id]['loja']]['nome']
    funcionarios_ausentes = usuarios[usuario_id]["ausencias"]  # Exemplo de como extrair informações

    # Criando o conteúdo do relatório como uma string
    conteudo = f"Relatório da Loja: {loja}\n\n"
    if not usuarios[usuario_id]["ausencias"]: # Se não houver funcionários ausentes, exibe "Todos entraram no horário normal."
       conteudo += f"Todos entraram no horário normal."
    # Iterar sobre os dados dos funcionários
    for funcionario, dados in funcionarios_ausentes.items():
        conteudo += f"Funcionário: {funcionario}\n"
        
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

def gerar_e_enviar_relatorios_consolidados():
    if not informacoes_diarias:
        print("Nenhuma informação para gerar relatórios.")
        return

    # Consolidando os dados de todas as lojas
    dados_consolidados = []
    for loja, ausencias in informacoes_diarias.items():
        for ausencia in ausencias:
            for funcionario, dados in ausencia.items():
                dados_consolidados.append({"Loja": loja, "Funcionário": funcionario, **dados})

    # Verifica se há dados para gerar os relatórios
    if dados_consolidados:
        # Gerar e enviar os relatórios consolidados (apenas uma vez)
        gerar_relatorio_pdf_consolidado("Consolidado", dados_consolidados)
        gerar_relatorio_excel_consolidado("Consolidado", dados_consolidados)
        
        # Enviar os relatórios para os responsáveis (apenas uma vez)
        enviar_relatorios_consolidados_para_responsavel("Consolidado", dados_consolidados)

    # Resetar o dicionário de informações diárias para o próximo dia
    informacoes_diarias.clear()
    print("Relatórios consolidados enviados e informações diárias resetadas.")


def enviar_relatorios_consolidados_para_responsavel(loja, dados_consolidados):
    responsavel_ids = [6566910217]  # IDs dos responsáveis
    for responsavel_id in responsavel_ids:
        # Enviar o PDF consolidado
        try:
            with open("relatorio_consolidado_todas_as_lojas.pdf", "rb") as pdf_file:
                bot.send_document(responsavel_id, pdf_file)
        except Exception as e:
            bot.send_message(responsavel_id, f"Erro ao enviar PDF consolidado: {e}")

        # Enviar o Excel consolidado
        try:
            with open("relatorio_consolidado_todas_as_lojas.xlsx", "rb") as excel_file:
                bot.send_document(responsavel_id, excel_file)
        except Exception as e:
            bot.send_message(responsavel_id, f"Erro ao enviar Excel consolidado: {e}")


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

def gerar_relatorio_excel_consolidado(nome_relatorio, dados_consolidados):
    # Verificando o conteúdo dos dados antes de gerar o relatório
    print(f"Dados Consolidados Recebidos: {dados_consolidados}")
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

# Agendar a execução da função ao final do dia (por exemplo, às 23:59)
schedule.every().day.at("23:00").do(gerar_e_enviar_relatorios_consolidados)
# Resetar o dicionário no início do dia
schedule.every().day.at("23:01").do(lambda: informacoes_diarias.clear())

#Reiniciar a conversa a qualquer momento
@bot.message_handler(func=lambda mensagem: usuarios.get(mensagem.chat.id, {}).get("finalizado", False))
def reiniciar_conversa(mensagem):
    usuario_id = mensagem.chat.id

    # Apagar completamente os dados do usuário
    if usuario_id in usuarios:
        del usuarios[usuario_id]  # Remove os dados do usuário completamente
    # Reiniciar a conversa chamando iniciar_conversa novamente
    iniciar_conversa(mensagem)

# Comando /reiniciar chama a função reiniciar_conversa
@bot.message_handler(commands=['reiniciar'])
def retomar_conversa(message):
    reiniciar_conversa(message)

bot.polling()