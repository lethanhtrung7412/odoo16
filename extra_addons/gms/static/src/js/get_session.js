/** @odoo-module **/
import { session } from "@web/session";

console.log('Cookie', session)
localStorage.setItem('userId', session.uid)

// // Function to add the script to the head
// function addChatbotScript() {
//     // Create a new script element
//     const script = document.createElement('script');
//     script.type = 'module';

//     // Define the script content
//     const scriptContent = `
//         import Chatbot from "https://cdn.jsdelivr.net/npm/flowise-embed/dist/web.js";
//         Chatbot.init({ 
//             chatflowid: "a2d9fed6-6633-4efd-a7b6-aa81affa09af", 
//             apiHost: "http://192.168.10.52:3000"
//         });
//     `;

//     // Add the script content to the script element
//     script.textContent = scriptContent;

//     // Append the script element to the head
//     document.head.appendChild(script);
// }

// // Call the function to add the script
// addChatbotScript();

    