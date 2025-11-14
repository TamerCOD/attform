// --- Telegram Configuration ---
const TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN';
const TELEGRAM_CHAT_ID = 'YOUR_TELEGRAM_CHAT_ID';

// This is the main server-side logic file.

function onOpen() {
  SpreadsheetApp.getUi()
      .createMenu('Certification')
      .addItem('Setup Sheets', 'setupSheets')
      .addSeparator()
      .addItem('Add Trainee', 'showAddTraineeForm')
      .addItem('Start Certification', 'showStartCertificationForm')
      .addItem('Create Ticket', 'showCreateTicketForm')
      .addSeparator()
      .addItem('Generate PDF', 'generatePdf')
      .addItem('Refresh Analytics', 'refreshAnalytics')
      .addToUi();
}

function setupSheets() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheets = {
    "Tickets": ["Ticket ID", "Questions", "Answers", "Category / Skill"],
    "Trainees": ["Full name", "Start date", "Mentor", "Skill / Direction", "Status"],
    "Archive": ["Ticket ID", "Trainee Name", "Timestamp", "Responsible mentor", "Scores"],
    "Analytics": ["Report Type", "Data"]
  };

  for (const sheetName in sheets) {
    let sheet = ss.getSheetByName(sheetName);
    if (!sheet) {
      sheet = ss.insertSheet(sheetName);
    }
    const headers = sheets[sheetName];
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  }
}

// --- Placeholder functions for menu items ---

function showAddTraineeForm() {
  const html = HtmlService.createHtmlOutputFromFile('TraineeForm')
      .setWidth(400)
      .setHeight(350);
  SpreadsheetApp.getUi().showModalDialog(html, 'Add New Trainee');
}

function addTrainee(traineeData) {
  const traineesSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Trainees');
  traineesSheet.appendRow([
    traineeData.fullName,
    traineeData.startDate,
    traineeData.mentor,
    traineeData.skill,
    "New" // Default status
  ]);
}

function showStartCertificationForm() {
  const html = HtmlService.createHtmlOutputFromFile('CertificationForm')
      .setWidth(400)
      .setHeight(250);
  SpreadsheetApp.getUi().showModalDialog(html, 'Start Certification');
}

function getTrainees() {
  const traineesSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Trainees');
  return traineesSheet.getRange(2, 1, traineesSheet.getLastRow() - 1, 1).getValues().flat();
}

function getSkills() {
  const ticketsSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Tickets');
  return ticketsSheet.getRange(2, 4, ticketsSheet.getLastRow() - 1, 1).getValues().flat();
}

function processCertification(certificationData) {
  const ticketsSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Tickets');
  const ticketData = ticketsSheet.getDataRange().getValues().find(row => row[3] === certificationData.skill);

  if (!ticketData) {
    SpreadsheetApp.getUi().alert('No ticket found for the selected skill.');
    return;
  }

  const template = HtmlService.createTemplateFromFile('AnswerForm');
  template.questions = JSON.parse(ticketData[1]);
  template.ticketId = ticketData[0];
  template.traineeName = certificationData.trainee;

  const html = template.evaluate().setWidth(800).setHeight(600);
  SpreadsheetApp.getUi().showModalDialog(html, 'Certification');
}

function gradeAnswers(submission) {
  const ticketsSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Tickets');
  const archiveSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Archive');
  const traineesSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Trainees');

  const ticketData = ticketsSheet.getDataRange().getValues().find(row => row[0] == submission.ticketId);
  const correctAnswers = JSON.parse(ticketData[2]);

  let score = 0;
  for (let i = 0; i < correctAnswers.length; i++) {
    if (submission.answers[i].trim().toLowerCase() === correctAnswers[i].trim().toLowerCase()) {
      score++;
    }
  }

  const traineeInfo = traineesSheet.getDataRange().getValues().find(row => row[0] === submission.traineeName);
  const mentorName = traineeInfo ? traineeInfo[2] : "Unknown";

  // Save to archive
  archiveSheet.appendRow([
    submission.ticketId,
    submission.traineeName,
    new Date(),
    mentorName,
    score
  ]);

  // Update trainee status
  const status = score > correctAnswers.length / 2 ? 'Passed' : 'Failed';
  const traineeRow = traineesSheet.getDataRange().getValues().findIndex(row => row[0] === submission.traineeName) + 1;
  if (traineeRow > 0) {
    traineesSheet.getRange(traineeRow, 5).setValue(status);
  } else {
    SpreadsheetApp.getUi().alert(`Could not find trainee "${submission.traineeName}" to update status.`);
  }

  // Send Telegram notification
  sendTelegramNotification(submission.traineeName, submission.ticketId, status);
}

function showCreateTicketForm() {
  const html = HtmlService.createHtmlOutputFromFile('TicketForm')
      .setWidth(800)
      .setHeight(600);
  SpreadsheetApp.getUi().showModalDialog(html, 'Create New Ticket');
}

function saveTicket(ticketData) {
  const ticketsSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Tickets');
  const newTicketId = ticketsSheet.getLastRow() > 0 ? ticketsSheet.getLastRow() : 1;
  ticketsSheet.appendRow([
    newTicketId,
    JSON.stringify(ticketData.questions),
    JSON.stringify(ticketData.answers),
    ticketData.category
  ]);
}

function generatePdf() {
  const ui = SpreadsheetApp.getUi();

  // Prompt for trainee name
  const traineeNameResponse = ui.prompt('Enter Trainee Name', 'Please enter the full name of the trainee to generate a report:', ui.ButtonSet.OK_CANCEL);
  if (traineeNameResponse.getSelectedButton() != ui.Button.OK) return;
  const traineeName = traineeNameResponse.getResponseText();

  // Find the latest record for the trainee in the Archive
  const archiveSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Archive');
  const archiveData = archiveSheet.getDataRange().getValues();
  const traineeRecords = archiveData.filter(row => row[1] === traineeName);
  if (traineeRecords.length === 0) {
    ui.alert('No records found for this trainee.');
    return;
  }
  const latestRecord = traineeRecords[traineeRecords.length - 1];
  const [ticketId, , timestamp, mentor, score] = latestRecord;

  // Find the ticket details
  const ticketsSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Tickets');
  const ticketsData = ticketsSheet.getDataRange().getValues();
  const ticketInfo = ticketsData.find(row => row[0] == ticketId);
  if (!ticketInfo) {
    ui.alert('Ticket information not found.');
    return;
  }
  const questions = JSON.parse(ticketInfo[1]);
  const category = ticketInfo[3];

  // Create a new Google Doc
  const doc = DocumentApp.create(`Certification - ${traineeName}`);
  const body = doc.getBody();
  body.appendParagraph('Certification Report').setHeading(DocumentApp.ParagraphHeading.TITLE);
  body.appendParagraph(`Trainee: ${traineeName}`);
  body.appendParagraph(`Date: ${new Date(timestamp).toLocaleDateString()}`);
  body.appendParagraph(`Mentor: ${mentor}`);
  body.appendParagraph(`Skill: ${category}`);
  body.appendParagraph(`Score: ${score}/${questions.length}`);
  body.appendHorizontalRule();

  questions.forEach((question, i) => {
    body.appendParagraph(`Question ${i+1}: ${question}`);
  });

  body.appendParagraph(`\n\nMentor Signature: _________________________`);
  doc.saveAndClose();

  // Create PDF and show link
  const pdf = DriveApp.getFileById(doc.getId()).getAs('application/pdf');
  const pdfFile = DriveApp.createFile(pdf).setName(doc.getName() + '.pdf');
  DriveApp.getFileById(doc.getId()).setTrashed(true); // Delete the temp doc

  ui.alert('PDF Generated', `View the PDF here: ${pdfFile.getUrl()}`, ui.ButtonSet.OK);
}

function refreshAnalytics() {
  const archiveSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Archive');
  const analyticsSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Analytics');
  const ticketsSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Tickets');

  const archiveData = archiveSheet.getLastRow() > 1 ? archiveSheet.getRange(2, 1, archiveSheet.getLastRow() - 1, 5).getValues() : [];
  if (archiveData.length === 0) {
    analyticsSheet.clear();
    analyticsSheet.getRange(1, 1, 1, 2).setValues([["Report Type", "Data"]]);
    analyticsSheet.appendRow(["Total Certifications", 0]);
    return;
  }

  const ticketsData = ticketsSheet.getDataRange().getValues().slice(1).reduce((obj, row) => {
    obj[row[0]] = { questions: JSON.parse(row[1]) };
    return obj;
  }, {});

  let passedCount = 0;
  archiveData.forEach(row => {
    const ticketId = row[0];
    const score = row[4];
    const ticket = ticketsData[ticketId];
    if (ticket && (score > ticket.questions.length / 2)) {
      passedCount++;
    }
  });

  const totalCerts = archiveData.length;
  const totalScore = archiveData.reduce((sum, row) => sum + row[4], 0);
  const averageScore = totalCerts > 0 ? totalScore / totalCerts : 0;
  const passRate = totalCerts > 0 ? (passedCount / totalCerts) * 100 : 0;

  analyticsSheet.clear();
  analyticsSheet.getRange(1, 1, 1, 2).setValues([["Report Type", "Data"]]);
  analyticsSheet.appendRow(["Total Certifications", totalCerts]);
  analyticsSheet.appendRow(["Average Score", averageScore.toFixed(2)]);
  analyticsSheet.appendRow(["Pass Rate", `${passRate.toFixed(2)}%`]);

  SpreadsheetApp.getUi().alert('Analytics have been refreshed.');
}

function sendTelegramNotification(traineeName, ticketId, result) {
  if (TELEGRAM_BOT_TOKEN === 'YOUR_TELEGRAM_BOT_TOKEN' || TELEGRAM_CHAT_ID === 'YOUR_TELEGRAM_CHAT_ID') {
    Logger.log('Telegram bot token or chat ID is not set.');
    return;
  }
  const message = `Certification Result:\n\nTrainee: ${traineeName}\nTicket: ${ticketId}\nResult: ${result}`;
  const url = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`;
  const options = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify({
      chat_id: TELEGRAM_CHAT_ID,
      text: message
    })
  };
  UrlFetchApp.fetch(url, options);
}
