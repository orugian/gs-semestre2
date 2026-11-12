import {render, screen} from '@testing-library/react';
import {expect, test} from 'vitest';

import App from '../src/App';

test('renderiza um botão Astryx dentro do tema', () => {
  render(<App />);

  const botao = screen.getByRole('button', {name: 'Astryx ativo'});
  expect(botao.tagName).toBe('BUTTON');
  expect(screen.getByRole('heading', {name: 'CitizenTech'})).toBeTruthy();
});
