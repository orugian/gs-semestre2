export const TEXTOS_JORNADA = {
  titulo: 'Minha transição',
  personaDemo: 'Persona de demonstração',
  sair: 'Sair',
  sessaoExpirada: 'Sua sessão foi encerrada. Entre novamente para continuar.',

  etapas: {
    consentimentos: 'Consentimentos',
    curriculo: 'Currículo',
    competencias: 'Competências',
  },

  auth: {
    entrar: 'Entrar',
    criarConta: 'Criar conta',
    email: 'E-mail',
    senha: 'Senha',
    senhaCurta: 'A senha deve ter pelo menos 10 caracteres.',
    alternarParaCriar: 'Ainda não tem conta? Criar conta',
    alternarParaEntrar: 'Já tem conta? Entrar',
    erroGenericoLogin: 'Não foi possível entrar. Verifique seus dados.',
  },

  consentimentos: {
    titulo: 'Autorizações de uso de dados',
    descricao:
      'Escolha de forma independente o que você autoriza no CitizenTech. Você pode revogar suas autorizações a qualquer momento.',
    finalidades: {
      perfil: {
        titulo: 'Perfil e currículo',
        descricao: 'Guardar o perfil e o texto redigido do currículo.',
      },
      curriculo_llm: {
        titulo: 'Sugestões com inteligência artificial',
        descricao:
          'Enviar o texto redigido e confirmado ao modelo de linguagem para sugerir competências.',
        avisoRevogacao:
          'Ao revogar esta autorização, novas sugestões automáticas de competências ficam bloqueadas.',
      },
      laboratorio_nuvem: {
        titulo: 'Laboratório na nuvem',
        descricao:
          'Enviar leituras e relato redigido do laboratório para a nuvem.',
      },
    },
    ativoDesde: (data: string) => `Ativo desde ${data}`,
    naoConcedido: 'Não concedido',
    revogadoEm: (data: string) => `Revogado em ${data}`,
    conceder: 'Conceder',
    revogar: 'Revogar',
    avancarCurriculo: 'Continuar para o currículo',
  },

  curriculo: {
    titulo: 'Envio de currículo',
    descricao:
      'Envie seu currículo colando o texto ou anexando um arquivo PDF ou DOCX. Antes de qualquer análise, tentamos ocultar seus dados de contato, e você revisa o resultado.',
    bloqueioConsentimentoPerfil:
      'Para enviar seu currículo, é necessário autorizar o armazenamento do perfil.',
    irParaConsentimentos: 'Ir para consentimentos',
    abaTexto: 'Colar texto',
    abaArquivo: 'Enviar arquivo',
    placeholderTexto: 'Cole aqui as experiências e formação do seu currículo...',
    rotuloTexto: 'Texto das experiências',
    rotuloArquivo: 'Arquivo do currículo (PDF ou DOCX até 2 MB)',
    enviarTexto: 'Processar texto',
    enviarArquivo: 'Processar arquivo',
    arquivoInvalido: 'Selecione um arquivo PDF ou DOCX.',
    arquivoGrande: 'Arquivo inválido ou maior que 2 MB.',
    textoRedigidoTitulo: 'Texto com dados protegidos',
    textoRedigidoDescricao:
      'Revise o texto abaixo. A ocultação automática de contatos e identificadores é parcial: apague o que ainda identificar você antes de confirmar.',
    confirmarEnvio: 'Confirmar e liberar para sugestões',
    sugerirCompetencias: 'Sugerir competências',
    sugerindo: 'Gerando sugestões...',
    limiteSugestoesAtingido: 'Limite de 5 sugestões em 24 horas atingido.',
    servicoIndisponivel:
      'O serviço de sugestões está indisponível agora; seu texto continua salvo e você pode tentar mais tarde.',
    consentimentoLlmNecessario:
      'É necessário conceder a autorização de uso do modelo de linguagem para sugerir competências.',
  },

  competencias: {
    titulo: 'Revisão de competências',
    avisoHonesto:
      'Sugestões automáticas: confirme apenas o que você realmente faz. Declarar não é o mesmo que demonstrar.',
    vazioTitulo: 'Nenhuma competência sugerida',
    vazioDescricao:
      'Envie e confirme seu currículo na etapa anterior para receber sugestões de competências.',
    grupos: {
      pendentes: 'Pendentes de revisão',
      confirmadas: 'Confirmadas',
      naoPossuo: 'Não possuo',
      rejeitadas: 'Rejeitadas',
    },
    acoes: {
      confirmar: 'Confirmar',
      naoPossuo: 'Não possuo',
      rejeitar: 'Rejeitar',
      editarTrecho: 'Editar trecho',
      salvar: 'Salvar confirmação',
      cancelar: 'Cancelar',
    },
    explicacoes: {
      rejeitar: 'A sugestão não corresponde ao texto do currículo.',
      naoPossuo: 'Você afirma que não possui esta competência.',
    },
    descartadasNota: (qtd: number) =>
      qtd === 1
        ? '1 sugestão foi descartada por não ter trecho correspondente no texto.'
        : `${qtd} sugestões foram descartadas por não terem trecho correspondente no texto.`,
  },
};

export function formatarDataHora(dataIso: string | null | undefined): string {
  if (!dataIso) return '—';
  try {
    const data = new Date(dataIso);
    return new Intl.DateTimeFormat('pt-BR', {
      timeZone: 'America/Sao_Paulo',
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(data);
  } catch {
    return dataIso;
  }
}
