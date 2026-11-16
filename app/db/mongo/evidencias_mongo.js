// CitizenTech: consultas de evidência (Data Science) — MongoDB (mongosh)
// Banco: MongoDB Atlas do projeto (nome em MONGODB_DB). Execução sem expor a URI:
//   docker exec -i -e MONGODB_URI -e MONGODB_DB citizentech-mongo-1 sh -c 'mongosh "$MONGODB_URI" --quiet' < evidencias_mongo.js
// Nenhuma consulta devolve texto de currículo ou de resposta: só metadados, contagens e hashes.

const banco = db.getSiblingDB(process.env.MONGODB_DB);
const mostrar = (titulo, valor) => { print(`\n== ${titulo}`); printjson(valor); };

// M1. Coleções e quantidade de documentos
mostrar("M1. Documentos por coleção",
  banco.getCollectionNames().sort().map((n) => ({colecao: n, documentos: banco.getCollection(n).countDocuments({})})));

// M2. Currículos redigidos por origem e status (sem o texto)
mostrar("M2. curriculos_redigidos por origem e status", banco.curriculos_redigidos.aggregate([
  {$group: {_id: {origem: "$origem", status: "$status"}, total: {$sum: 1},
            emails_redigidos: {$sum: "$redacoes.email"}, telefones_redigidos: {$sum: "$redacoes.telefone"}}},
  {$sort: {"_id.origem": 1, "_id.status": 1}},
]).toArray());

// M3. Extrações de competências pela LLM: modelo usado, candidatas e descartes (sem resposta bruta)
mostrar("M3. extracoes_llm por modelo", banco.extracoes_llm.aggregate([
  {$group: {_id: "$modelo", extracoes: {$sum: 1}, media_candidatas: {$avg: "$contagem_candidatas"},
            fora_da_lista: {$sum: "$descartadas.fora_da_lista"}, sem_trecho: {$sum: "$descartadas.sem_trecho"},
            trecho_nao_encontrado: {$sum: "$descartadas.trecho_nao_encontrado"}}},
  {$sort: {extracoes: -1}},
]).toArray());

// M4. Model cards dos modelos de mercado (procedência e promoção)
mostrar("M4. model_cards", banco.model_cards.find({},
  {_id: 0, modelo: 1, tipo: 1, status_promocao: 1, periodo_treino: 1, periodo_validacao: 1, seed: 1,
   "versoes.sklearn": 1, "sha256_artefatos.metricas.json": 1}).sort({modelo: 1}).toArray());

// M5. Avaliações da resposta aberta em cache: nível médio por critério da rubrica
mostrar("M5. avaliacoes_llm: nível médio por critério", banco.avaliacoes_llm.aggregate([
  {$unwind: "$criterios"},
  {$group: {_id: {exercicio: "$exercicio_id", criterio: "$criterios.id"}, avaliacoes: {$sum: 1},
            nivel_medio: {$avg: "$criterios.nivel"}}},
  {$sort: {"_id.exercicio": 1, "_id.criterio": 1}},
]).toArray());

// M6. Respostas abertas guardadas (redigidas): quantidade por pessoa, sem o texto
mostrar("M6. respostas_abertas por usuário", banco.respostas_abertas.aggregate([
  {$group: {_id: "$usuario_id", respostas: {$sum: 1}, ultima: {$max: "$criado_em"}}},
  {$sort: {respostas: -1}}, {$limit: 10},
]).toArray());

// M7. Índices existentes (desempenho e unicidade)
mostrar("M7. Índices por coleção", banco.getCollectionNames().sort().map((n) => ({
  colecao: n, indices: banco.getCollection(n).getIndexes().map((i) => i.name)})));
