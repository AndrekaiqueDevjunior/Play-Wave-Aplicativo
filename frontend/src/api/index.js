/**
 * api/index.js
 * Ponto central de exportação de toda a camada de API FastAPI.
 *
 * Uso:
 *   import { dispositivos, campanhas, midias, audio, relatorios } from '@/api';
 *
 * Ou direto:
 *   import { buscarPlaylistDispositivo } from '@/api/dispositivos';
 *
 * Quando VITE_API_URL não estiver definido, as funções retornam null
 * e o app continua usando Base44 como fonte de dados.
 */

export * as dispositivos from "./dispositivos";
export * as campanhas from "./campanhas";
export * as midias from "./midias";
export * as audio from "./audio";
export * as relatorios from "./relatorios";
export * as localizacoes from "./localizacoes";
export * as tenants from "./tenants";
export { isApiConfigurada, verificarSaude, getBaseUrl } from "./http";
