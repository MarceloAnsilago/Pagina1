import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Instituto Tarumã Pesquisa", page_icon="🌲")

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
    conn.commit()
    conn.close()

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
    try:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO rejeicao (candidato, token) VALUES (?, ?)', (candidato, token))
        conn.commit()
        st.write("Rejeição registrada com sucesso!")  # Log de depuração
    except Exception as e:
        st.error(f"Erro ao registrar rejeição: {e}")
    finally:
        conn.close()

# Função para carregar as configurações atuais
def carregar_configuracoes():
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute('SELECT exibir_real, candidato_favorecido FROM configuracao WHERE id = 1')
    config = cursor.fetchone()
    conn.close()
    return config

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

# Função principal do Streamlit
def main():
    st.title("🌲 Instituto Tarumã Pesquisa")

    # Criar as tabelas se ainda não existirem
    criar_tabelas()

    # Capturar token da URL
    # query_params = st.query_params
    query_params = st.experimental_get_query_params()

    token_url = query_params.get('token', None)

    # Carregar as configurações de gráficos
    config = carregar_configuracoes()
    if config:
        exibir_real, candidato_favorecido = config
    else:
        st.error("Erro ao carregar as configurações.")
        return

    if token_url and len(token_url) > 0:
        token_url = token_url[0] if isinstance(token_url, list) else token_url

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
                        candidato = st.radio(
                            "Escolha o candidato:",
                            ('Fabio de Paula', 'Coronel Crispim', 'Prof Eudes', 'Branco/Nulo', 'Não sei/Não decidi')
                        )
                        submit_voto = st.form_submit_button("Votar")
                        if submit_voto:
                            registrar_intencao_voto(candidato, token_url)
                            marcar_token_como_usado_intencao(token_url)
                            st.success(f"Seu voto em {candidato} foi registrado com sucesso!")
                            st.plotly_chart(gerar_grafico_intencao_voto(candidato_favorecido if not exibir_real else None))

                if not usado_rejeicao:
                    st.success("Link válido para rejeição.")
                    with st.form(key='rejeicao'):
                        st.write("Em qual desses candidatos você não votaria de jeito nenhum?")
                        rejeicao = st.radio(
                            "Escolha o candidato:",
                            ('Fabio de Paula', 'Coronel Crispim', 'Prof Eudes')
                        )
                        submit_rejeicao = st.form_submit_button("Registrar rejeição")
                        if submit_rejeicao:
                            st.write(f"Registrando rejeição para {rejeicao}")  # Log de depuração
                            registrar_rejeicao(rejeicao, token_url)
                            marcar_token_como_usado_rejeicao(token_url)
                            st.success(f"Sua rejeição para {rejeicao} foi registrada com sucesso!")
                            st.plotly_chart(gerar_grafico_rejeicao(candidato_favorecido if not exibir_real else None))
    else:
        st.error("Link não fornecido na URL. Adicione ?token=SEU_TOKEN à URL.")

if __name__ == "__main__":
    main()
