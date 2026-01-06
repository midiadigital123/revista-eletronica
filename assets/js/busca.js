/**
 * Esse arquivo contém as funções específicas para consultar a URL do JSON passado.
 */

async function getData(URL) {
    
const file = URL;
  try {
    const response = await fetch(file);

    if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
    }

    const result = await response.json();
    return result;
  } catch (error) {
    console.error(error.message);
  }
}

export { getData };
