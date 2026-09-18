import en from './en.json';

export default function t(key) {
  return key.split('.').reduce((acc, part) => (acc || {})[part], en) || key;
}
