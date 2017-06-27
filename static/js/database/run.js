$(document).ready(function() {
	function build() {
		var data = {};
		data['repeat'] = $("input[name='regular']:checked").val();
		data['mode'] = $("input[name='result-process']:checked").val();
		data['data'] = {}
		if(data['repeat'] == 'once') {
			data['data']['date'] = $("input[name='date-input']").val(); 
			data['data']['time'] = $("input[name='time-input']").val();
		}
		if(data['repeat'] == 'everyday') {
			data['data']['time'] = $("input[name='time-input']").val();
		}
		if(data['repeat'] == 'custom') {
			$(".week-wrap").each(function() {
				if(!$(this).hasClass('active')) 
					return;
				data['data'][$(this).attr('itemprop').trim()] = $(this).find("input").val()
			}); 
		}

		return data;
	}

	$(".date-input").hide();
	$(".time-input").hide();
	$(".custom-radio").click(function() {
		$(this).siblings().removeClass('active');
		$(this).addClass('active');
		if(!$(this).parent().hasClass("schedule-options"))
			return; 

		if(this.innerText != 'Custom') {
			$(".weekday").addClass('disabled');
			$(".week-wrap input").attr('disabled', true)
		} else {
			$(".weekday").removeClass('disabled');
			$(".week-wrap input").attr('disabled', false)
			$(".date-input").hide();
			$(".time-input").hide();
		}
		if(this.innerText == 'Everyday') {
			$(".date-input").hide();
			$(".time-input").show();
		}
		if(this.innerText == 'Once') {
			$(".date-input").show();
			$(".time-input").show();
		}
	}); 
	$(".weekday").click(function() {
		$(this).toggleClass('btn-primary');
		$(this).parent().toggleClass('active');
		var radio = $(".schedule-options .custom-radio");
		radio[radio.length-1].click();
	}); 
	$("#save-run-configuration").click(function() {
		var data = build();
		$.post(
			url, {
				data: JSON.stringify(data), 
				csrfmiddlewaretoken: csrf
			}, function(r) {
				console.log(r);
			} ); 
	}); 

	console.log($("input[name='regular']").val());

	$("input[value='"+interval['repeat']+"']").parent().click();
	$("input[value='"+interval['mode']+"'").parent().click();

	if($("input[name='regular']:checked").val() == 'everyday') {
		$("input[name='time-input']").val(interval['data']['time']);
	}
	if($("input[name='regular']:checked").val() == 'once') {
		$("input[name='date-input']").val(interval['data']['date']);
		$("input[name='time-input']").val(interval['data']['time']);
	}
	if($("input[name='regular']:checked").val() == 'custom') {
		for(item in interval['data']) {
			$(".week-wrap[itemprop='"+item+"'] > div").click();
			$(".week-wrap[itemprop='"+item+"'] > input").val(interval['data'][item])
			console.log(item);
		}
	}

	$("#run-now").click(function() {
		var btn = $(this);
		var show_data = $("#show-data"); 
		var icon = $("#running");
		icon.show();
		btn.attr('disabled', true); 
		show_data.attr('disabled', true); 
		$.post(
			execute_url, 
			{ 
				'now': true,
				'csrfmiddlewaretoken': csrf, 
			}, 
			function(r) {
				r = JSON.parse(r);
				console.log(r);
				icon.hide();
				btn.attr('disabled', false); 
				show_data.attr('disabled', false); 
			} )
	}); 

	$("#show-data").click(function() {
		$.post(
			execute_url, 
			{
				'show-data': true,
				'csrfmiddlewaretoken': csrf
			}, function(r) {
				r = JSON.parse(r);
				var container = $("#data-area"); 
				var content = ""
				for(var url in r) {
					content += "<h4>"+url+"</h4> <table class='table' > <thead> <tr>";
					for(var key in r[url][0]) {
						content += "<th>"+key+"</th>";
					}
					content += "</tr></thead><tbody>";
					for(var i = 0; i < r[url].length; i ++) {
						content += "<tr>";
						for(var key in r[url][i]) {
							content += "<td>"+r[url][i][key]+"</td>";
						}
						content += "</tr>";
					}
					content += "</tbody></table>"
				}
				content += "<a href='"+download_result_url+"' class='btn btn-default pull-right'> DOwnload Result </a>"
				container.html(content);
			} )
	}); 

}); 
