import 'dotenv/config';
import { Mastra } from '@mastra/core/mastra';
import { PinoLogger } from '@mastra/loggers';

import { weatherAgent } from './agents/weather-agent';
import { telloAgent } from './agents/tello-agent';

export const mastra = new Mastra({
  agents: { weatherAgent, telloAgent },
  logger: new PinoLogger({
    name: 'Mastra',
    level: 'info',
  }),
});
