function crearCertificados() {
    
    const templateId = '1E6GSfVyTHN0xgc_pranAbVGLRfpui1z0xWHzH5Qjjw8'; // Reemplaza con el ID de documento base como modelo
    const sheet_id = '1uCW3L_VTQcvwreg_z-OsXZ3N0zvGTb4e8_Zkc48RqPc'; // Cambia esto por el ID de tu hoja de cálculo
    const sheet_name = 'IMPORTRANGE SUPERVISION'; // Cambia esto por el nombre de tu hoja de cálculo
    const folderId = '1nuplc1Fax_ThYcLAgsxAcB8Dyh-PALqc'; // Opcional: ID de la carpeta donde guardar certificados

    // Obtener la hoja de cálculo y la hoja activa
    const sheet = SpreadsheetApp.openById(sheet_id).getSheetByName(sheet_name); //toma la hoja
    const data = sheet.getDataRange().getValues(); // Obtiene todos los datos de la hoja

    // Obtener la carpeta de destino en Google Drive
    const folder = DriveApp.getFolderById(folderId);

    for (var i = 1; i < data.length; i++) { // Empieza desde la segunda fila
        var row = data[i];
        const fecha = row[0];
          
                //APARTIR DE FECHA PARTICIONAR Y FORMATEAR TEXTO A PARTIR DE LA MARCA TEMPORAL DEL CUESTIONARIO (PRIMERA COLUMNA ESTANDAR)
                const timestamp = row[0]; 
                const date = new Date(timestamp);

                // Obtener las partes de la fecha
                const day = String(date.getDate()).padStart(2, '0');
                const month = String(date.getMonth() + 1).padStart(2, '0'); // Los meses en JavaScript van de 0 a 11
                const year = date.getFullYear();
                const hours = String(date.getHours()).padStart(2, '0');
                const minutes = String(date.getMinutes()).padStart(2, '0');
                const seconds = String(date.getSeconds()).padStart(2, '0');

                // Formatear la fecha
                const formattedDate = `${day}/${month}/${year} ${hours}:${minutes}:${seconds}`;

        //continua con el resto de celdas (DEFINIR VARIABLES)
        var num_ot = row[i]; //VARIARI i SEGUN CANTIDAD DE COLUMNAS A TRAER 
        
        
        //genera google docs
        var doc = DriveApp.getFileById(templateId).makeCopy('N° OT ' + num_ot, DriveApp.getFolderById(folderId));
        var docId = doc.getId();
        var docBody = DocumentApp.openById(docId).getBody();
        var footer = DocumentApp.openById(docId).getFooter();


        // Reemplazar marcadores de posición con datos
        docBody.replaceText('{{Marca temporal}}', formattedDate); //FORMATO PARA REMPLAZAR TEXTO DE LA CELDA EN HOJA MODELO DOCS
        

        // Insertar imágenes desde Google Drive
        insertImage(docBody, '{{FOTO VEHICULO SEÑALIZADO}}', foto_veh, 200); //FORMATO PARA REMPLAZAR IMAGEN DE LA CELDA (LINK DRIVE) EN HOJA MODELO DOCS
     
    
        DocumentApp.openById(docId).saveAndClose(); //guarda el documento y lo cierra

        Logger.log('Certificado creado: ' + num_ot); //nombre del documento

         // Convertir el documento a PDF
        const pdfFile = DriveApp.getFileById(doc.getId()).getAs('application/pdf');
        folder.createFile(pdfFile);
        
        // Eliminar el documento de Google Docs después de convertirlo a PDF
        DriveApp.getFileById(doc.getId()).setTrashed(true);
    }
}

//funcion para insertar imagen desde link almacenado en celda. imagen guardada en google drive
function insertImage(docBody, placeholder, fileUrl, maxWidth) {
    if (isValidDriveUrl(fileUrl)) {
        try {
            const fileId = extractFileIdFromUrl(fileUrl);
            if (fileId) {
                const file = DriveApp.getFileById(fileId);
                const imageBlob = file.getBlob();
                
                // Reemplazar el marcador de posición con la imagen
                const searchResult = docBody.findText(placeholder);
                if (searchResult) {
                    const element = searchResult.getElement();
                    const parent = element.getParent();
                    parent.removeChild(element);
                    
                    // Insertar la imagen en lugar del texto
                    const paragraph = parent.asParagraph();
                    paragraph.clear(); // Limpiar el párrafo de contenido
                    const img = paragraph.appendInlineImage(imageBlob);
                    
                    // Ajustar el tamaño de la imagen
                    img.setWidth(300); // Ajusta el ancho máximo
                    img.setHeight(360); // Ajustar la altura proporcionalmente img.getHeight() * (maxWidth / img.getWidth())
                }
            } else {
                Logger.log('Invalid file URL: ' + fileUrl);
            }
        } catch (e) {
            Logger.log('Error fetching image with URL: ' + fileUrl + ' - ' + e.message);
        }
    } else {
        Logger.log('Empty or invalid file URL: ' + fileUrl);
    }
}

function extractFileIdFromUrl(url) {
    const regex = /[?&]id=([^&]+)/;
    const match = url.match(regex);
    return match ? match[1] : null;
}

function isValidDriveUrl(url) {
    // Check if the URL is a valid Google Drive link
    const regex = /^https:\/\/drive\.google\.com\/.*[?&]id=([^&]+)/;
    return regex.test(url);
}


