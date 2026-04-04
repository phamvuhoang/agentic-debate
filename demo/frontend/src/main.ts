import { bootstrapApp } from './app/bootstrap';
import './styles/app.css';

const mount = document.getElementById('app');
if (mount) {
  bootstrapApp(mount).catch(console.error);
}
