import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from io import BytesIO
import uuid


# Configuração da página deve ser a primeira chamada
st.set_page_config(page_title="Instituto Tarumã Pesquisa", page_icon="🌲")

# Injetando o CSS para esconder o ícone do GitHub e outros elementos indesejados
hide_github_icon = """
    <style>
    .css-1jc7ptx, .e1ewe7hr3, .viewerBadge_container__1QSob, .styles_viewerBadge__1yB5_, 
    .viewerBadge_link__1S137, .viewerBadge_text__1JaDK { 
        display: none; 
    }
    #MainMenu { 
        visibility: hidden; 
    } 
    footer { 
        visibility: hidden; 
    } 
    header { 
        visibility: hidden; 
    }
    </style>
"""

# Aplicando o estilo ao Streamlit
st.markdown(hide_github_icon, unsafe_allow_html=True)






# Função para conectar ao banco de dados
def conectar_banco():
    return sqlite3.connect('enquete.db')

# Função para criar as tabelas necessárias, se não existirem
def criar_tabelas():
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tokens (
        token TEXT PRIMARY KEY,
        usado_intencao BOOLEAN NOT NULL DEFAULT FALSE,
        usado_rejeicao BOOLEAN NOT NULL DEFAULT FALSE
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS intencao_voto (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidato TEXT NOT NULL,
        token TEXT NOT NULL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rejeicao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidato TEXT NOT NULL,
        token TEXT NOT NULL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS configuracao (
        id INTEGER PRIMARY KEY,
        exibir_real BOOLEAN NOT NULL,
        candidato_favorecido TEXT,
        data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    # Inserir configuração inicial, se não existir
    cursor.execute('''
    INSERT OR IGNORE INTO configuracao (id, exibir_real, candidato_favorecido) 
    VALUES (1, TRUE, NULL)
    ''')
    conn.commit()
    conn.close()

# Função para carregar as configurações atuais
def carregar_configuracoes():
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute('SELECT exibir_real, candidato_favorecido FROM configuracao WHERE id = 1')
    config = cursor.fetchone()
    conn.close()
    return config

# Função para salvar as configurações
def salvar_configuracoes(exibir_real, candidato_favorecido=None):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE configuracao SET 
        exibir_real = ?,
        candidato_favorecido = ?,
        data_hora = CURRENT_TIMESTAMP
        WHERE id = 1
    ''', (exibir_real, candidato_favorecido))
    conn.commit()
    conn.close()

# =======================================
# Código da Página do Usuário
# =======================================

# Função para verificar o estado do token
def verificar_token(token):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute('SELECT usado_intencao, usado_rejeicao FROM tokens WHERE token = ?', (token,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado

# Função para marcar o token como usado na intenção de voto
def marcar_token_como_usado_intencao(token):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute('UPDATE tokens SET usado_intencao = TRUE WHERE token = ?', (token,))
    conn.commit()
    conn.close()

# Função para marcar o token como usado na rejeição
def marcar_token_como_usado_rejeicao(token):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute('UPDATE tokens SET usado_rejeicao = TRUE WHERE token = ?', (token,))
    conn.commit()
    conn.close()

# Função para registrar a intenção de voto
def registrar_intencao_voto(candidato, token):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO intencao_voto (candidato, token) VALUES (?, ?)', (candidato, token))
    conn.commit()
    conn.close()

# Função para registrar a rejeição
def registrar_rejeicao(candidato, token):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO rejeicao (candidato, token) VALUES (?, ?)', (candidato, token))
    conn.commit()
    conn.close()

# Função para exibir a tabela `configuracao` como dataframe
def exibir_dataframe_configuracao():
    conn = conectar_banco()
    df = pd.read_sql_query("SELECT * FROM configuracao", conn)
    conn.close()
    return df

# Função para exibir a tabela de tokens
def exibir_tokens():
    conn = conectar_banco()
    df = pd.read_sql_query("SELECT * FROM tokens", conn)
    conn.close()
    return df

# Função para exibir a tabela de intenção de votos
def exibir_tabela_intencao_votos():
    conn = conectar_banco()
    df = pd.read_sql_query("SELECT * FROM intencao_voto", conn)
    conn.close()
    return df

# Função para exibir a tabela de rejeição
def exibir_tabela_rejeicao():
    conn = conectar_banco()
    df = pd.read_sql_query("SELECT * FROM rejeicao", conn)
    conn.close()
    return df

# Função para zerar os tokens
def zerar_tokens():
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute('UPDATE tokens SET usado_intencao = FALSE, usado_rejeicao = FALSE')
    conn.commit()
    conn.close()

# Função para zerar a tabela de intenção de votos
def zerar_intencao_votos():
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM intencao_voto')
    conn.commit()
    conn.close()

# Função para zerar a tabela de rejeição
def zerar_rejeicao():
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM rejeicao')
    conn.commit()
    conn.close()

# Função para gerar o gráfico de rosca para intenção de voto
def gerar_grafico_intencao_voto(candidato_favorecido=None):
    conn = conectar_banco()
    df = pd.read_sql_query("SELECT candidato, COUNT(*) as votos FROM intencao_voto GROUP BY candidato", conn)
    conn.close()

    # Manipular dados se houver um candidato favorecido e gráfico vantajoso estiver ativado
    if candidato_favorecido:
        df = trocar_votos(df, candidato_favorecido, 'votos')

    total_participantes = df['votos'].sum()
    fig = px.pie(df, names='candidato', values='votos', hole=0.4, title=f'Intenção de Voto ({total_participantes} participantes)')
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(showlegend=False)
    return fig

# Função para gerar o gráfico de rosca para rejeição
def gerar_grafico_rejeicao(candidato_favorecido=None):
    conn = conectar_banco()
    df = pd.read_sql_query("SELECT candidato, COUNT(*) as rejeicoes FROM rejeicao GROUP BY candidato", conn)
    conn.close()

    # Manipular dados se houver um candidato favorecido e gráfico vantajoso estiver ativado
    if candidato_favorecido:
        df = trocar_rejeicoes(df, candidato_favorecido)

    total_participantes = df['rejeicoes'].sum()
    fig = px.pie(df, names='candidato', values='rejeicoes', hole=0.4, title=f'Rejeição ({total_participantes} participantes)')
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(showlegend=False)
    return fig

# Função para trocar votos se o gráfico vantajoso estiver ativado
def trocar_votos(df, candidato_favorecido, coluna):
    if candidato_favorecido and candidato_favorecido in df['candidato'].values:
        max_value = df[coluna].max()
        candidato_mais_votado = df.loc[df[coluna] == max_value, 'candidato'].values[0]
        # Trocar os valores entre o candidato favorecido e o candidato com maior votação
        df.loc[df['candidato'] == candidato_mais_votado, coluna] = df.loc[df['candidato'] == candidato_favorecido, coluna].values[0]
        df.loc[df['candidato'] == candidato_favorecido, coluna] = max_value
    return df

# Função para trocar rejeições se o gráfico vantajoso estiver ativado
def trocar_rejeicoes(df, candidato_favorecido):
    if candidato_favorecido and candidato_favorecido in df['candidato'].values:
        max_rejeicoes = df['rejeicoes'].max()
        candidato_mais_rejeitado = df.loc[df['rejeicoes'] == max_rejeicoes, 'candidato'].values[0]
        
        if candidato_mais_rejeitado == candidato_favorecido:
            segundo_mais_rejeitado = df.loc[df['rejeicoes'] != max_rejeicoes, 'rejeicoes'].max()
            
            # Verificar se o segundo candidato existe antes de tentar acessar
            if not df[df['rejeicoes'] == segundo_mais_rejeitado].empty:
                segundo_candidato = df.loc[df['rejeicoes'] == segundo_mais_rejeitado, 'candidato'].values[0]
                
                # Trocar os valores entre o candidato favorecido e o segundo mais rejeitado
                df.loc[df['candidato'] == segundo_candidato, 'rejeicoes'] = max_rejeicoes
                df.loc[df['candidato'] == candidato_favorecido, 'rejeicoes'] = segundo_mais_rejeitado
    return df

# Função para validar o token
def validar_token(token_url):
    if token_url == "admin-Ro4143":
        return "admin"
    elif token_url == "gr@f1c=0":
        return "grafico"
    else:
        conn = conectar_banco()
        cursor = conn.cursor()
        cursor.execute('SELECT token FROM tokens WHERE token = ?', (token_url,))
        resultado = cursor.fetchone()
        conn.close()
        if resultado:
            return "user"
        else:
            return None

# # Páginas separadas
# def pagina_usuario(token_url):
#     st.title("🌲 Instituto Tarumã Pesquisa")

#     # Criar as tabelas se ainda não existirem
#     criar_tabelas()

#     # Carregar as configurações de gráficos
#     config = carregar_configuracoes()
#     if config:
#         exibir_real, candidato_favorecido = config
#     else:
#         st.error("Erro ao carregar as configurações.")
#         return

#     if token_url and len(token_url) > 0:
#         # Verificar o estado do token no banco de dados
#         resultado = verificar_token(token_url)
        
#         if resultado is None:
#             st.error("Link não encontrado no banco de dados.")
#         else:
#             usado_intencao, usado_rejeicao = resultado

#             # Mostrar gráficos e formulários baseados no estado do token
#             if usado_intencao and usado_rejeicao:
#                 st.info("Seu voto já foi computado, obrigado por participar!")
#                 st.plotly_chart(gerar_grafico_intencao_voto(candidato_favorecido if not exibir_real else None))
#                 st.markdown("---")  # Separador entre os gráficos
#                 st.plotly_chart(gerar_grafico_rejeicao(candidato_favorecido if not exibir_real else None))
#             else:
#                 if not usado_intencao:
#                     st.success("Link válido para intenção de voto.")
#                     with st.form(key='intencao_voto'):
#                         st.write("Se as eleições em São Miguel do Guaporé fossem hoje, em qual desses candidatos você votaria?")
#                         candidato = st.radio(
#                             "Escolha o candidato:",
#                             ('Selecione uma opção', 'Fabio de Paula', 'Coronel Crispim', 'Prof Eudes', 'Branco/Nulo', 'Não sei/Não decidi')
#                         )
#                         submit_voto = st.form_submit_button("Votar")

#                         if candidato != 'Selecione uma opção' and submit_voto:
#                             # Continuar o processo de votação
#                             registrar_intencao_voto(candidato, token_url)
#                             marcar_token_como_usado_intencao(token_url)
#                             st.success(f"Seu voto em {candidato} foi registrado com sucesso! Atualize a página para ver o resultado!")
#                             st.plotly_chart(gerar_grafico_intencao_voto(candidato_favorecido if not exibir_real else None))
#                         elif candidato == 'Selecione uma opção' and submit_voto:
#                             st.warning("Você precisa selecionar um candidato antes de votar.")

#                 if not usado_rejeicao:
#                     st.success("Link válido para rejeição.")
#                     with st.form(key='rejeicao'):
#                         st.write("Em qual desses candidatos você não votaria de jeito nenhum?")
#                         rejeicao = st.radio(
#                             "Escolha o candidato:",
#                             ('Selecione uma opção', 'Fabio de Paula', 'Coronel Crispim', 'Prof Eudes')
#                         )
#                         submit_rejeicao = st.form_submit_button("Registrar rejeição")
                        
#                         if rejeicao != 'Selecione uma opção' and submit_rejeicao:
#                             registrar_rejeicao(rejeicao, token_url)
#                             marcar_token_como_usado_rejeicao(token_url)
#                             st.success(f"Sua rejeição para {rejeicao} foi registrada com sucesso! Atualize a página para ver o resultado!")
#                             # Exibir ambos os gráficos após o registro de rejeição
#                             st.plotly_chart(gerar_grafico_intencao_voto(candidato_favorecido if not exibir_real else None))
#                             st.markdown("---")  # Separador entre os gráficos
#                             st.plotly_chart(gerar_grafico_rejeicao(candidato_favorecido if not exibir_real else None))
#                         elif rejeicao == 'Selecione uma opção' and submit_rejeicao:
#                             st.warning("Você precisa selecionar um candidato antes de registrar a rejeição.")

#     else:
#         st.error("Link não fornecido na URL. Adicione ?token=SEU_TOKEN à URL.")
def pagina_usuario(token_url):
    st.title("🌲 Instituto Tarumã Pesquisa")

    # Criar as tabelas se ainda não existirem
    criar_tabelas()

    # Carregar as configurações de gráficos
    config = carregar_configuracoes()
    if config:
        exibir_real, candidato_favorecido = config
    else:
        st.error("Erro ao carregar as configurações.")
        return

    if token_url and len(token_url) > 0:
        # Verificar o estado do token no banco de dados
        resultado = verificar_token(token_url)
        
        if resultado is None:
            st.error("Link não encontrado no banco de dados.")
        else:
            usado_intencao, usado_rejeicao = resultado

            # Mostrar gráficos e formulários baseados no estado do token
            if usado_intencao and usado_rejeicao:
                st.info("Seu voto já foi computado, obrigado por participar!")
                st.plotly_chart(gerar_grafico_intencao_voto(candidato_favorecido if not exibir_real else None))
                st.markdown("---")  # Separador entre os gráficos
                st.plotly_chart(gerar_grafico_rejeicao(candidato_favorecido if not exibir_real else None))
            else:
                if not usado_intencao:
                    st.success("Link válido para intenção de voto.")
                    with st.form(key='intencao_voto'):
                        st.write("Se as eleições em São Miguel do Guaporé fossem hoje, em qual desses candidatos você votaria?")
                        candidato = st.selectbox(
                            "Escolha o candidato:",
                            ['', 'Fabio de Paula', 'Coronel Crispim', 'Prof Eudes', 'Branco/Nulo', 'Não sei/Não decidi']
                        )
                        submit_voto = st.form_submit_button("Votar")

                        if candidato != '' and submit_voto:
                            # Continuar o processo de votação
                            registrar_intencao_voto(candidato, token_url)
                            marcar_token_como_usado_intencao(token_url)
                            st.success(f"Seu voto em {candidato} foi registrado com sucesso! Atualize a página para ver o resultado!")
                            st.plotly_chart(gerar_grafico_intencao_voto(candidato_favorecido if not exibir_real else None))
                        elif candidato == '' and submit_voto:
                            st.warning("Você precisa selecionar um candidato antes de votar.")

                if not usado_rejeicao:
                    st.success("Link válido para rejeição.")
                    with st.form(key='rejeicao'):
                        st.write("Em qual desses candidatos você não votaria de jeito nenhum?")
                        rejeicao = st.selectbox(
                            "Escolha o candidato:",
                            ['', 'Fabio de Paula', 'Coronel Crispim', 'Prof Eudes']
                        )
                        submit_rejeicao = st.form_submit_button("Registrar rejeição")
                        
                        if rejeicao != '' and submit_rejeicao:
                            registrar_rejeicao(rejeicao, token_url)
                            marcar_token_como_usado_rejeicao(token_url)
                            st.success(f"Sua rejeição para {rejeicao} foi registrada com sucesso! Atualize a página para ver o resultado!")
                            # Exibir ambos os gráficos após o registro de rejeição
                            st.plotly_chart(gerar_grafico_intencao_voto(candidato_favorecido if not exibir_real else None))
                            st.markdown("---")  # Separador entre os gráficos
                            st.plotly_chart(gerar_grafico_rejeicao(candidato_favorecido if not exibir_real else None))
                        elif rejeicao == '' and submit_rejeicao:
                            st.warning("Você precisa selecionar um candidato antes de registrar a rejeição.")

    else:
        st.error("Link não fornecido na URL. Adicione ?token=SEU_TOKEN à URL.")


# =======================================
# Código da Página de Configurações (Admin)
# =======================================     
#    
# Função para converter DataFrame para Excel e CSV para download
def converter_para_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def converter_para_csv(df):
    return df.to_csv(index=False).encode('utf-8')
def criar_tokens(quantidade):
    conn = conectar_banco()
    cursor = conn.cursor()
    for _ in range(quantidade):
        token = str(uuid.uuid4())
        cursor.execute('INSERT INTO tokens (token) VALUES (?)', (token,))
    conn.commit()
    conn.close()


def exibir_e_gerar_download_tokens():
    st.subheader("Visualização dos Tokens")
    df_tokens = exibir_tokens()
    st.dataframe(df_tokens)

    # Botões para download dos tokens em Excel e CSV
    st.download_button(
        label="Baixar Tokens (Excel)",
        data=converter_para_excel(df_tokens),
        file_name="tokens.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.download_button(
        label="Baixar Tokens (CSV)",
        data=converter_para_csv(df_tokens),
        file_name="tokens.csv",
        mime="text/csv"
    )

def pagina_admin():
    st.title("Configurações")

    # Criar as tabelas se ainda não existirem
    criar_tabelas()

    # Exibir opções de configuração
    st.subheader("Configurações dos Gráficos")
    
    config = carregar_configuracoes()
    if config:
        exibir_real, candidato_favorecido = config
    else:
        st.error("Erro ao carregar as configurações.")
        exibir_real = True  # Valor padrão se ocorrer erro ao carregar
        candidato_favorecido = None

    # Checkbox para exibir gráficos reais
    exibir_real = st.checkbox("Exibir gráficos reais", value=exibir_real)

    # Exibir combobox e dataframe se "Exibir gráficos reais" for desmarcado
    if not exibir_real:
        st.subheader("Seleção do Candidato Favorecido")
        candidato_favorecido = st.selectbox(
            "Escolha o candidato que deve ser favorecido:",
            ("Fabio de Paula", "Coronel Crispim", "Prof Eudes")
        )
        st.write("O candidato selecionado receberá a maior votação quando estiver em desvantagem e a menor rejeição quando ele não for o menos rejeitado.")

        # Exibir a tabela de configuração como dataframe
        st.subheader("Visualização da Tabela de Configuração")
        df = exibir_dataframe_configuracao()
        st.dataframe(df)

        # Adicionar legenda explicativa
        st.write("Legenda: **1** para 'Sim' (Exibir gráficos reais), **0** para 'Não' (Não exibir gráficos reais)")

    # Botão para salvar as configurações
    if st.button("Salvar Configurações"):
        salvar_configuracoes(exibir_real, candidato_favorecido)
        st.success("Configurações salvas com sucesso.")

    # Separador
    st.markdown("---")
    
    # Exibição da tabela de tokens com botão para atualizar e baixar em Excel
    st.subheader("Visualização da Tabela de Tokens")
    df_tokens = exibir_tokens()
    st.dataframe(df_tokens)
    
    if st.button("Atualizar Tabela de Tokens"):
        df_tokens = exibir_tokens()
        st.dataframe(df_tokens)
        st.success("Tabela de Tokens atualizada.")

    st.download_button(
        label="Baixar Tokens (Excel)",
        data=converter_para_excel(df_tokens),
        file_name="tokens.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Separador acima do botão de download
    st.markdown("---")

    # Botões para download dos votos
    st.subheader("Download de Votos")

    df_intencao = exibir_tabela_intencao_votos()
    df_rejeicao = exibir_tabela_rejeicao()

    # Exibir tabelas de intenção de votos e rejeição com botões para atualizar
    st.subheader("Visualização da Tabela de Intenção de Votos")
    st.dataframe(df_intencao)
    if st.button("Atualizar Tabela de Intenção de Votos"):
        df_intencao = exibir_tabela_intencao_votos()
        st.dataframe(df_intencao)
        st.success("Tabela de Intenção de Votos atualizada.")

    st.subheader("Visualização da Tabela de Rejeição")
    st.dataframe(df_rejeicao)
    if st.button("Atualizar Tabela de Rejeição"):
        df_rejeicao = exibir_tabela_rejeicao()
        st.dataframe(df_rejeicao)
        st.success("Tabela de Rejeição atualizada.")

    # Separador acima do botão de download
    st.markdown("---")

    # Download de intenção de votos em Excel e CSV
    st.download_button(
        label="Baixar Intenção de Votos (Excel)",
        data=converter_para_excel(df_intencao),
        file_name="intencao_votos.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.download_button(
        label="Baixar Intenção de Votos (CSV)",
        data=converter_para_csv(df_intencao),
        file_name="intencao_votos.csv",
        mime="text/csv"
    )

    # Separador para a opção de zerar banco de dados
    st.markdown("---")

    # Checkbox para zerar banco de dados
    if st.checkbox("Zerar banco de dados"):
        st.warning("Essa ação não pode ser desfeita. Selecione as opções abaixo para zerar:")

        # Botão para zerar tokens
        if st.button("Zerar Tokens"):
            zerar_tokens()
            st.success("Todos os tokens foram zerados com sucesso.")
            # Reexibir os tokens após zerar para verificar se deu certo
            df_tokens = exibir_tokens()
            st.dataframe(df_tokens)

        # Botão para zerar intenção de votos
        if st.button("Zerar Intenção de Votos"):
            zerar_intencao_votos()
            st.success("Todos os votos de intenção foram zerados com sucesso.")
            df_intencao = exibir_tabela_intencao_votos()
            st.dataframe(df_intencao)
        
        # Botão para zerar rejeição
        if st.button("Zerar Rejeição"):
            zerar_rejeicao()
            st.success("Todas as rejeições foram zeradas com sucesso.")
            df_rejeicao = exibir_tabela_rejeicao()
            st.dataframe(df_rejeicao)

    # Separador para a criação de tokens
    st.markdown("---")

    # Criação de tokens
    st.subheader("Criação de Tokens")
    quantidade_tokens = st.number_input("Quantos tokens deseja criar?", min_value=1, value=1000, step=1)
    if st.button("Criar Tokens"):
        criar_tokens(quantidade_tokens)
        st.success(f"{quantidade_tokens} tokens foram criados com sucesso!")
        # Exibir os tokens após a criação
        df_tokens = exibir_tokens()
        st.dataframe(df_tokens)



# =======================================
# Código da Nova Página de Gráficos
# =======================================

def pagina_graficos():
    st.title("📊 Exibição de Gráficos")

    # Criar as tabelas se ainda não existirem
    criar_tabelas()

    # Carregar as configurações de gráficos
    config = carregar_configuracoes()
    if config:
        exibir_real, candidato_favorecido = config
    else:
        st.error("Erro ao carregar as configurações.")
        return

    # Exibir o primeiro gráfico conforme a configuração atual
    st.subheader("Gráfico Atual (Configuração Atual)")
    st.plotly_chart(gerar_grafico_intencao_voto(candidato_favorecido if not exibir_real else None))
    st.plotly_chart(gerar_grafico_rejeicao(candidato_favorecido if not exibir_real else None))

    st.markdown("---")  # Separador entre os gráficos

    # Exibir o gráfico real, independentemente da configuração
    st.subheader("Gráfico Real (Dados Reais)")
    st.plotly_chart(gerar_grafico_intencao_voto(None))  # Gráfico real, sem ajustes
    st.plotly_chart(gerar_grafico_rejeicao(None))  # Gráfico real, sem ajustes

# =======================================
# Código Principal para Selecionar a Página Correta
# =======================================
def main():
    # Capturar token da URL
    query_params = st.query_params
    token_url = query_params.get('token', None)
    token_url = token_url[0] if isinstance(token_url, list) else token_url

    # Validar o token
    pagina = validar_token(token_url)

    if pagina == "admin":
        pagina_admin()
    elif pagina == "user":
        pagina_usuario(token_url)
    elif token_url == "gr@f1c=0":
        pagina_graficos()
    else:
        st.warning("Você precisa de um link válido para participar.")
        # Exibir gráficos como na página do usuário
        st.plotly_chart(gerar_grafico_intencao_voto())
        st.markdown("---")  # Separador entre os gráficos
        st.plotly_chart(gerar_grafico_rejeicao())

if __name__ == "__main__":
    main()
