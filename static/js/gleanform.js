
$(document).ready(function(){   
	var $datefield = $("#id_date");
	$("#id_date").datepicker();
   var infos = {
      "title": "This is the name of your glean." +
               "It is how you will identify" +
               "this glean from others on" +
               "this day or week, and it" +
               "also will also be the default" +
               "Title to any Announcement" +
               "Emails that are sent.",
      "description": "Description of the Glean. " +
               "This text will appear on the glean" +
               " page and in the email announcement " +
               "received by your volunteers. Include " +
               "information to best prepare your " +
               "gleaners; i.e. weather, type of " +
               "crop to be gleaned.",
      "counties": "County. A county should already " +
               "be selected. If not, please select " +
               "appropriate county and any additional " +
               "counties in close proximity to farm " +
               "location, i.e. Poultney VT farm, " +
               "could select Washington NY County " +
               "in addition to Rutland County. " +
               "Volunteers receive announcements " +
               "based on the county they selected " +
               "to glean in.",
      "farm": "By Choosing a farm (and optionally " +
               "a Farm Location) the remainder of " +
               "the form auto-populates with Farm-" +
               "specific Data.",
               
   };
   for (var i=0; i<Object.keys(infos).length; i++) {
      (function(i){
         var key = Object.keys(infos)[i];
         var value = infos[key];
         var pop_name = key + "_popover";
         $("label[for='id_" + key +"']").append(
            "<div class='pull-right'><a id='" + pop_name + "'><i class='icon-info-sign'></i></a></div>"
         );
         $("#" + pop_name).tooltip({
            "title": value,
            "trigger": "hover",
         })
      })(i)
   }
})
function clear_checkboxes(){
	var $boxes = $("input[type='checkbox']");
  $boxes.prop("checked", false);
}
function updateAddressFields(data){
   $('#id_instructions').val(data['instructions']);
   $('#id_directions').val(data['directions']);
   $('#id_address_one').val(data['address_one']);
   $('#id_address_two').val(data['address_two']);
   $('#id_city').val(data['city']);
   $('#id_state').val(data['state']);
   $('#id_zipcode').val(data['zipcode']);
   $('#id_counties').children().prop("selected", false);
   
   clear_checkboxes();

   $("input[type='checkbox'][value=" + data["counties"] + "]")
   	.prop("checked", true);
}
function clearAddressFields(){
   $('#id_instructions').val('');
   $('#id_directions').val('');
   $('#id_address_one').val('');
   $('#id_address_two').val('');
   $('#id_city').val('');
   $('#id_state').val('');
   $('#id_zipcode').val('');
   $('#id_counties').children().prop("selected", false);
}
function updateFarmLocationChoices(data){
   var locations = data['farm_locations'];
      $('#id_farm_location').children().remove()
      $.each(locations, function(val, text){
         $('#id_farm_location').append(
            $('<option></option>').val(val).html(text)
            );
      });
      $('#id_farm_location').children([text="---------"]).prop("selected", true)
}
function clearFarmLocationChoices(){
   $('#id_farm_location').children().remove()
}

// This is the key code \\
$(function() {
    /*
   $("input[type='checkbox']").on("click", function(event){
		clear_checkboxes();
		$(event.target).prop("checked", true);
   });
  */
   $('#id_farm').change(function(){
      var farm = $(this).children("option:selected").val();
      if (farm != "") {
         $.ajax({
            url:"/api/farm/"+farm,
            success: function(data){
               $('#id_address_one').text(data['address_one']);
               updateAddressFields(data);
               updateFarmLocationChoices(data);
         },
      });

      } else {
               clearAddressFields();
               clearFarmLocationChoices();
      } 
   });         
   
   $('#id_farm_location').change(function(){
      var farm = $('#id_farm').children("option:selected").val();
      var selection = $(this).children("option:selected").val();
      if (selection != "") {
         $.ajax({
            url:"/api/farmlocation/"+farm+'/'+selection,
            success: function(data){
               updateAddressFields(data);
         },
      });

      } else {
         clearAddressFields();
      }
   });
   clearFarmLocationChoices();
});

