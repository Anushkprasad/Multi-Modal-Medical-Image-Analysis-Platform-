import { jsPDF } from 'jspdf';
import html2canvas from 'html2canvas';

export const generatePDF = async (elementId, filename = 'report.pdf') => {
  const element = document.getElementById(elementId);
  if (!element) {
    throw new Error(`Element with id ${elementId} not found`);
  }

  try {
    const canvas = await html2canvas(element, {
      scale: 2,
      useCORS: true,
      logging: false,
      backgroundColor: '#071a2b',
    });

    const imgData = canvas.toDataURL('image/png');
    const pdf = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4',
    });

    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = pdf.internal.pageSize.getHeight();
    
    const imgProps = pdf.getImageProperties(imgData);
    const imgRatio = imgProps.width / imgProps.height;
    
    let finalWidth = pdfWidth;
    let finalHeight = pdfWidth / imgRatio;

    if (finalHeight > pdfHeight) {
      finalHeight = pdfHeight;
      finalWidth = pdfHeight * imgRatio;
    }

    const marginX = (pdfWidth - finalWidth) / 2;
    const marginY = 10;

    pdf.addImage(imgData, 'PNG', marginX, marginY, finalWidth, finalHeight);
    pdf.save(filename);
    
    return true;
  } catch (error) {
    console.error('Error generating PDF:', error);
    throw error;
  }
};
