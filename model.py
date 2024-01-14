# # <!DOCTYPE html>
# # <html lang="en">
# # <head>
# #     <meta charset="UTF-8">
# #     <meta name="viewport" content="width=device-width, initial-scale=1.0">
# #     <title>Mother Health Risk Assessment</title>
# #     <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
# #     <style>
# #         body {
# #             font-family: 'Arial', sans-serif;
# #             background-color: #f4f7f6;
# #             color: #333;
# #         }
# #         .container {
# #             background-color: white;
# #             border-radius: 8px;
# #             padding: 20px;
# #             margin-top: 20px;
# #             box-shadow: 0 2px 4px rgba(0,0,0,0.1);
# #         }
# #         .risk-level {
# #             font-weight: bold;
# #             color: #dc3545; /* Red color for risk */
# #         }
# #         .suggestions-list {
# #             list-style-type: none;
# #             padding: 0;
# #         }
# #         .suggestions-list li {
# #             margin-bottom: 10px;
# #         }
# #         .content-section {
# #             margin-bottom: 20px;
# #         }
# #     </style>
# # </head>
# # <body>

# <div class="container mt-5">
#         <h2 class="text-center mb-4"><strong>Mother Health Risk Assessment Result</strong></h2>
#         <div class="content-section">
#             <h4>Risk Level: <span class="risk-level">{{ assessment.interpretation }}</span></h4>
#         </div>
        
#         <div class="content-section">
#             <h4>Suggestions Based on Your Score</h4>
#             <ul class="suggestions-list">
#                 {% for suggestion in assessment.suggestions %}
#                     <li>{{ suggestion }}</li>
#                 {% endfor %}
#             </ul>
#         </div>
        
#         <div class="content-section">
#             <h4>General Health Suggestions</h4>
#             <ul class="suggestions-list">
#                 {% for general_suggestion in assessment.general_suggestions %}
#                     <li>{{ general_suggestion }}</li>
#                 {% endfor %}
#             </ul>
#         </div>
                    
#     </div>
# # <!-- Bootstrap JS -->
# # <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
# # </body>
# # </html>
