import {MOTIVOS_REQUISITO} from '../dominio/rotulos';

export const TEXTOS_JORNADA = {
  titulo: 'Minha transição',
  personaDemo: 'Persona de demonstração',
  sair: 'Sair',

  etapas: {
    consentimentos: 'Consentimentos',
    intencao: 'Intenção',
    curriculo: 'Currículo',
    competencias: 'Competências',
    comparacao: 'Comparação',
    plano: 'Plano',
    exercicio: 'Exercício',
    laboratorio: 'Laboratório',
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
    conceder: 'Conceder',
    revogar: 'Revogar',
    avancarCurriculo: 'Continuar para a intenção',
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
    descartadasNota: (qtd: number) =>
      qtd === 1
        ? '1 sugestão foi descartada por não ter trecho correspondente no texto.'
        : `${qtd} sugestões foram descartadas por não terem trecho correspondente no texto.`,
  },

  intencao: {
    titulo: 'Intenção profissional',
    descricao:
      'Informe suas metas profissionais, tempo disponível e localização para orientar suas opções de transição.',
    atividades: {
      titulo: 'Atividades desejadas',
      descricao:
        'Liste as atividades que você gostaria de realizar (até 10 atividades, cada uma com até 120 caracteres).',
      nova: 'Nova atividade desejada',
      adicionar: 'Adicionar atividade',
      remover: 'Remover',
      limite: 'Limite de até 10 atividades desejadas atingido.',
      tamanhoInvalido: 'Cada atividade deve ter entre 1 e 120 caracteres.',
      vazio: 'Nenhuma atividade adicionada ainda.',
    },
    motivos: {
      titulo: 'Motivos da transição',
      descricao:
        'Explique seus motivos e expectativas (até 5 motivos, cada um com até 300 caracteres). Antes de salvar, tentamos ocultar dados de contato; o texto salvo aparece abaixo para você conferir.',
      novo: 'Novo motivo',
      adicionar: 'Adicionar motivo',
      remover: 'Remover',
      limite: 'Limite de até 5 motivos atingido.',
      tamanhoInvalido: 'Cada motivo deve ter até 300 caracteres.',
      vazio: 'Nenhum motivo adicionado ainda.',
    },
    horas: {
      rotulo: 'Horas por semana disponíveis',
      descricao: 'Informe quantas horas semanais você pode dedicar (entre 1 e 80 horas).',
      erro: 'As horas por semana devem ser entre 1 e 80.',
    },
    orcamento: {
      rotulo: 'Orçamento mensal para qualificação (R$)',
      descricao:
        'Opcional. Valor estimado que você pode investir mensalmente em capacitação (até R$ 100.000).',
      erro: 'O orçamento mensal deve ser entre R$ 0 e R$ 100.000.',
    },
    uf: {
      rotulo: 'Unidade Federativa (UF)',
      descricao: 'Selecione o estado onde você reside ou deseja atuar.',
      selecione: 'Selecione uma UF',
      erro: 'Selecione uma UF válida.',
    },
    salvar: 'Salvar intenção',
    salvando: 'Salvando intenção...',
    salvoEm: (data: string) => `Salvo em ${data}`,
    bloqueioPerfil:
      'Para salvar sua intenção profissional, é necessário conceder a autorização de perfil e currículo.',
    irParaConsentimentos: 'Ir para consentimentos',
    avancar: 'Continuar para o currículo',
  },

  comparacao: {
    titulo: 'Comparação de destinos',
    descricao:
      'Escolha de 1 a 3 destinos para comparar lado a lado requisitos, evidências, mercado formal observado e disponibilidade.',
    selecao: {
      titulo: 'Escolha até 3 destinos',
      descricao: 'Selecione os destinos profissionais que deseja comparar.',
      limiteMaximo: 'Você pode selecionar no máximo 3 destinos para comparar.',
      nenhumSelecionado: 'Selecione pelo menos 1 destino para comparar.',
      comparar: 'Comparar',
      comparando: 'Comparando destinos...',
      ufRotulo: 'UF para dados de mercado (opcional)',
    },
    avisoSemNota:
      'Sem nota única: cada dimensão é apresentada separadamente e a decisão é sua.',
    legenda: {
      titulo: 'Legenda dos estados de evidência',
      demonstrada:
        'Demonstrada: evidência revisada por critério explícito (exercício)',
      declarada: 'Declarada: informada pela pessoa, não comprovada',
      desconhecida: 'Desconhecida: informação insuficiente, não inaptidão',
      lacuna:
        'Lacuna: ausência identificada (a pessoa disse que não possui, ou o exercício ficou abaixo do mínimo)',
    },
    novaComparacao: 'Nova comparação',
    obrigatoriosNaoAtendidos: {
      titulo: 'Obrigatórios ainda não atendidos',
      todosDemonstrados: 'todos os obrigatórios demonstrados',
    },
    contagem: {
      titulo: 'Balanço de evidências',
      demonstrada: 'Demonstradas',
      declarada: 'Declaradas',
      desconhecida: 'Desconhecidas',
      lacuna: 'Lacunas',
    },
    requisitos: {
      titulo: 'Lista de requisitos por estado',
      obrigatorio: 'obrigatório',
      avisoConflito: 'informações conflitantes; revise suas competências',
      motivos: MOTIVOS_REQUISITO,
    },
    mercado: {
      titulo: 'Mercado formal observado',
      natureza: 'Observado',
      rotuloValor: 'admissões formais estimadas no grupo e território',
      verNoMercado: 'ver no Mercado',
      motivosIndisponivel: {
        uf_nao_informada: 'Informe a UF para ver o mercado observado',
        snapshot_indisponivel: 'Dados de mercado indisponíveis no momento',
        sem_serie_para_uf: 'Sem série observada para esta UF',
      },
    },
    preferencias: {
      titulo: 'Disponibilidade e preferências',
      semConflitos: 'Nenhum conflito identificado com sua disponibilidade.',
    },
    escolherDestino: 'Escolher este destino',
    dialogSubstituir: {
      titulo: 'Substituir plano anterior?',
      descricao:
        'Você já possui um plano ativo. Ao escolher um novo destino, o plano anterior será substituído pelo novo plano inicial.',
      confirmar: 'Substituir plano',
      cancelar: 'Cancelar',
    },
  },

  plano: {
    titulo: 'Plano de desenvolvimento',
    vazioTitulo: 'Nenhum plano ativo',
    vazioDescricao:
      'Escolha um destino na comparação para gerar seu plano inicial com checkpoints.',
    irParaComparacao: 'Comparar destinos',
    carregando: 'Carregando plano de desenvolvimento...',
    avisoFixo:
      'Concluir um checkpoint não torna a competência demonstrada; apenas o exercício diagnóstico com critério explícito comprova a evidência.',
    secaoCheckpoints: 'Checkpoints do plano',
    secaoJaDemonstrados: 'Já demonstradas anteriormente',
    secaoObservacoes: 'Observações do plano',
    obrigatorio: 'Obrigatório',
    opcional: 'Opcional',
    criterioConclusao: 'Critério de conclusão',
    status: {
      pendente: 'Pendente',
      em_andamento: 'Em andamento',
      concluido: 'Concluído',
    },
    tipos: {
      estudar: 'Estudar',
      praticar: 'Praticar',
      demonstrar: 'Demonstrar',
      laboratorio: 'Laboratório',
      exercicio: 'Exercício diagnóstico',
    },
    acoes: {
      comecar: 'Começar',
      concluir: 'Concluir',
      fazerExercicio: 'Fazer o exercício',
      irParaLaboratorio: 'Acessar laboratório',
      concluirAria: (titulo: string) => `Concluir checkpoint ${titulo}`,
      comecarAria: (titulo: string) => `Começar checkpoint ${titulo}`,
    },
    resultadoExercicio: {
      titulo: 'Resultado da última tentativa',
    },
  },

  exercicio: {
    titulo: 'Exercício diagnóstico',
    carregando: 'Carregando exercício diagnóstico...',
    cenarioTitulo: 'Cenário',
    criteriosTitulo: 'Critérios da resposta aberta',
    criteriosDescricao:
      'Critérios avaliados com suas âncoras explícitas de nível (0, 1 e 2):',
    questoesObjetivasTitulo: 'Questões objetivas',
    questaoAbertaTitulo: 'Resposta aberta',
    rotuloRespostaAberta: 'Sua resposta aberta',
    contadorCaracteres: (qtd: number) => `${qtd} / 4000 caracteres (mínimo 20)`,
    tentativasRestantes: (qtd: number) =>
      `Tentativas restantes em 24h: ${qtd}`,
    limiteAtingido:
      'Você atingiu o limite de 3 tentativas em 24 horas para este exercício.',
    bloqueioConsentimentoLlm:
      'Para realizar o exercício diagnóstico com avaliação de resposta aberta, é necessário autorizar o uso do modelo de inteligência artificial.',
    irParaConsentimentos: 'Ir para consentimentos',
    enviar: 'Enviar resposta',
    enviando: 'Avaliando respostas...',
    resultadoTitulo: 'Resultado da tentativa',
    resultadoObjetiva: (acertos: number, total: number) =>
      `Objetiva: ${acertos} de ${total} acertos`,
    gabaritoRotulo: 'Gabarito',
    justificativaRotulo: 'Justificativa',
    respostaCorreta: 'Correta',
    respostaIncorreta: 'Incorreta',
    trechoCitacao: 'Trecho da resposta:',
    notaExercicio: (nota: number) => `Nota do exercício: ${nota}`,
    notaLlmRotulo: (nota: number) => `Nota aberta: ${nota}`,
    conceito: {
      demonstrada: 'Demonstrada (básico)',
      insuficiente: 'Insuficiente',
      parcial: 'Parcial',
    },
    explicacaoParcial:
      'a avaliação da resposta aberta não estava disponível; a parte objetiva foi registrada',
    rastreabilidade: {
      versao: (v: string) => `Versão ${v}`,
      modelo: (m: string) => `Modelo: ${m}`,
      data: (d: string) => `Realizado em ${d}`,
    },
    acoes: {
      refazer: 'Refazer exercício',
      discordo: 'Discordo',
    },
    contestacao: {
      titulo: 'Registrar discordância',
      descricao:
        'Se você discorda da avaliação, registre o motivo da sua contestação (entre 10 e 1000 caracteres). Isso não altera a nota automaticamente, mas fica registrado para auditoria.',
      rotuloMotivo: 'Motivo da discordância',
      placeholderMotivo: 'Explique por que você discorda da avaliação...',
      contador: (qtd: number) => `${qtd} / 1000 caracteres (mínimo 10)`,
      confirmar: 'Confirmar discordância',
      cancelar: 'Cancelar',
      registrada: (data?: string) =>
        data ? `Contestação registrada em ${data}` : 'Contestação registrada',
      jaRegistrada: 'Você já registrou uma contestação para esta tentativa.',
    },
    historico: {
      titulo: 'Histórico de tentativas',
      ultima: 'Última',
      melhor: 'Melhor',
    },
  },

  laboratorio: {
    titulo: 'Laboratório na nuvem',
    descricao:
      'Acompanhamento em tempo real da bancada de monitoramento IoT.',
    opcional: 'Esta etapa é opcional e destinada à prática com telemetria e sensores.',
    bloqueioConsentimento:
      'Para acessar o laboratório na nuvem, é necessário autorizar o envio de leituras e relato na etapa de consentimentos.',
    irParaConsentimentos: 'Ir para consentimentos',
    abrirSessao: 'Abrir sessão',
    abrindo: 'Iniciando sessão...',
    codigoSessao: 'Código da sessão',
    copiarCodigo: 'Copiar código',
    codigoCopiado: 'Código copiado!',
    instrucoesTitulo: 'Instruções',
    statusSessao: {
      ativa: 'Ativa',
      encerrada: 'Encerrada',
      expirada: 'Expirada',
    },
    leiturasTitulo: 'Leituras da bancada',
    atualizarLeituras: 'Atualizar leituras',
    atualizando: 'Atualizando leituras...',
    tabela: {
      horario: 'Horário (Brasília)',
      metrica: 'Métrica',
      valor: 'Valor',
      risco: 'Risco',
      estadoNuvem: 'Estado da nuvem',
    },
    riscos: {
      normal: 'Normal',
      atencao: 'Atenção',
      critico: 'Crítico',
    },
    indicadoresTitulo: 'Indicadores de telemetria',
    relatoTitulo: 'Relato de observação',
    rotuloRelato: 'Relato de observação da bancada',
    placeholderRelato:
      'Descreva anomalias ou observações da bancada (até 280 caracteres)...',
    contadorRelato: (qtd: number) => `${qtd} / 280 caracteres`,
    enviarRelato: 'Enviar relato',
    enviandoRelato: 'Enviando relato...',
    textoRedigidoTitulo: 'Relato registrado (texto com dados protegidos)',
    statusRelato: {
      pendente: 'será enviado com a próxima leitura',
      enviado: 'Enviado',
    },
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
