import {createRoot} from 'react-dom/client';
import Home from '../app/page';
import '../app/globals.css';
import '../app/i18n/zh.css';
createRoot(document.getElementById('root')!).render(<Home/>);
