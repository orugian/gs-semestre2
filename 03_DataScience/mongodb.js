// GS 2026.2 - Data Science - MongoDB (mongosh)
// Dados semiestruturados: payload bruto vindo dos dispositivos e relatos livres dos cidadãos.
// Executar: mongosh < mongodb.js
// TODO: ajustar coleções/campos à ideia e justificar a divisão Oracle x MongoDB no relatorio.md.

use("citizentech");

// ------------------------------------------------------------ documentos
db.leituras_brutas.insertMany([
  {
    dispositivo_id: "esp32-01", tipo_dispositivo: "esp32",
    localizacao: { type: "Point", coordinates: [0.0, 0.0] },   // [longitude, latitude]
    metrica: "TODO_metrica_1", valor: 75.0, status: "ALERTA",
    payload_original: { /* JSON exatamente como chegou */ },
    recebido_em: new Date()
  }
]);

db.relatos.insertMany([
  {
    cidadao_id: 1,                                   // id_cidadao no Oracle
    texto: "TODO relato do cidadão",
    analise_ia: { rotulo: "negative", confianca: 0.91 },
    anexos: [{ tipo: "foto", url: "TODO" }],
    tags: ["TODO"],
    criado_em: new Date()
  }
]);

db.leituras_brutas.createIndex({ localizacao: "2dsphere" });
db.leituras_brutas.createIndex({ dispositivo_id: 1, recebido_em: -1 });

// ------------------------------------------------------------ consultas
// 1) últimas leituras em alerta
db.leituras_brutas.find({ status: "ALERTA" }).sort({ recebido_em: -1 }).limit(10);

// 2) média e pico por métrica (agregação)
db.leituras_brutas.aggregate([
  { $group: { _id: "$metrica", media: { $avg: "$valor" }, pico: { $max: "$valor" }, total: { $sum: 1 } } }
]);

// 3) relatos classificados pela IA como negativos
db.relatos.find({ "analise_ia.rotulo": "negative" }, { texto: 1, "analise_ia": 1, _id: 0 });

// 4) leituras num raio de 2 km de um ponto
db.leituras_brutas.find({
  localizacao: { $near: { $geometry: { type: "Point", coordinates: [0.0, 0.0] }, $maxDistance: 2000 } }
});
