import 'dotenv/config';
import { Mastra } from '@mastra/core/mastra';
import { PinoLogger } from '@mastra/loggers';

import { telloAgent } from './agents/tello-agent';

export const mastra = new Mastra({
  agents: { telloAgent },
  logger: new PinoLogger({
    name: 'Mastra',
    level: 'info',
  }),
});
