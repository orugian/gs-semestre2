import {Button} from '@astryxdesign/core/Button';
import {Heading} from '@astryxdesign/core/Heading';
import {Text} from '@astryxdesign/core/Text';
import {Theme} from '@astryxdesign/core/theme';
import {neutralTheme} from '@astryxdesign/theme-neutral/built';

export default function App() {
  return (
    <Theme theme={neutralTheme}>
      <main className="mx-auto flex max-w-xl flex-col gap-4 p-8">
        <Heading level={1}>CitizenTech</Heading>
        <Text>Esqueleto da interface: componentes Astryx com Tailwind apenas no layout.</Text>
        <div className="flex gap-2">
          <Button label="Astryx ativo" variant="primary" />
        </div>
      </main>
    </Theme>
  );
}