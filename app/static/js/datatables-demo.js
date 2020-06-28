// Call the dataTables jQuery plugin
$(document).ready(function() {
  $('#dataTable').DataTable();
});

$('#dataTable > thead > tr > th').each(function(){
    console.log("Hello world");
})