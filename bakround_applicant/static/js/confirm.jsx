import Confirmation from './Confirmation.jsx';
import { createConfirmation } from 'react-confirm';

const confirm = createConfirmation(Confirmation);

// This is optional. But I recommend to define your confirm function easy to call.
export default function(confirmation, options = {}) {
  // Can pass whatever to the component. These arguments will be your Component's props
  return confirm({ confirmation, options });
}