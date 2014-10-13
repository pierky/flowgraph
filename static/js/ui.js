	GlobalConfig = {};
	Graphs = [];

	function UIError( s ) {
		alert( s );
	}

	function UIConfirm( s ) {
		return confirm(s);
	}

	function UISuccess() {
		alert( 'OK' );
	}

	function UIAjaxError( Descr, jqXHR, textStatus, errorThrown ) {
		ErrMsg = Descr;
		try {
			ErrMsg += ': ' + textStatus;
			ErrMsg += '\n' + jqXHR.responseText;
		} finally {
			return ErrMsg;
		}
	}

	function UIGetGraph() {
		var Graph = {};
		var Query = {};

		// ID

		Graph['ID'] = $('[name=graphid]').val().trim();

		// Title

		Graph['Title'] = $('[name=title]').val().trim();
		if( Graph['Title'] == '' ) {
			UIError( 'Missing title' );
			return;
		}

		// Sources

		Query['SourceFiles'] = {};

		Query['SourceFiles']['BaseDir'] = $('[name=basedir]').val().trim();
		Query['SourceFiles']['FileNameFormat'] = $('[name=filenameformat]').val().trim();
		Query['SourceFiles']['Interval'] = $('[name=interval]').val().trim();

		if( Query['SourceFiles']['Interval'] != '' ) {
			if( ! /^\+?[1-9]\d*$/.test( Query['SourceFiles']['Interval'] ) ) {
				UIError( 'Invalid netflow file interval' );
				return;
			}
		}

		Query['SourceFiles']['SourceIDs'] = [];

		$('[name=sources] option:selected').each( function() {
			Query['SourceFiles']['SourceIDs'].push( $(this).val() );
		} );

		if( Query['SourceFiles']['SourceIDs'].length == 0 ) {
			UIError( 'No source selected' );
			return;
		}

		// Filter

		Query['Filter'] = $('[name=filter]').val().trim();

		// Aggregation field

		SelAggr = UIGetSelectedAggr();

		if( ! SelAggr ) {
			UIError( 'Invalid aggregation field selected' );
			return;
		}

		// Aggregation field optional argument

		if( SelAggr['ArgRequired'] ) {
			Query['AggrFieldArg'] = $('[name=arg]').val().trim();

			if( Query['AggrFieldArg'] == '' ) {
				UIError( 'Argument required for this aggregation field' );
				return;
			}
		}

		Query['AggrField'] = SelAggr['ID'];

		if( SelAggr['AggrType_s'] ) {
			Query['AggrType'] = 's';
		} else {
			Query['AggrType'] = 'A';
		}

		// TopN

		Query['TopN'] = $('[name=top]').val().trim();

		if( Query['TopN'] == '' ) {
			UIError( 'Missing top N limit' );
			return;
		} else {
			if( ! /^\+?[1-9]\d*$/.test( Query['TopN'] ) ) {
				UIError( 'Invalid top N limit' );
				return;
			} else {
				Query['TopN'] = parseInt( Query['TopN'] );
			}
		}

		// Order by

		Query['OrderBy'] = {};

		Query['OrderBy']['ColName'] = $('[name=orderby]').val().trim();
		Query['OrderBy']['Order'] = $('[name=orderby_dir]').val().trim();

		// Draw

		Graph['Draw'] = {};
		Graph['Draw']['What'] = $('[name=draw_what]').val();
		Graph['Draw']['How'] = $('[name=draw_how]').val();

		// Cache file name

		Query['CacheFile'] = $('[name=cachefilename]').val().trim();

		// Schedules

		if( $('[name=enable_scheduling]').is(':checked') ) {
			if ( $('#schedules div').length > 0 ) {
				Graph['Scheduler'] = {};
				Graph['Scheduler']['Schedules'] = $('#schedules div').map( function() { return $(this).data( 'Schedule' ); } ).get();

				if( $('[name=scheduler_maxcache]').val() != '' ) {
					if( ! /^\+?[1-9]\d*$/.test( $('[name=scheduler_maxcache]').val() ) ) {
						UIError( 'Invalid value for the Scheduler option "Keep data for max ... days".' );
						return;
					}
					Graph['Scheduler']['MaxCache'] = parseInt( $('[name=scheduler_maxcache]').val() );
				}
			} else {
				UIError( 'Scheduler enabled but no schedules defined.' );
				return;
			}
		}

		Graph['Query'] = Query;

		return Graph;
	}

	function UISaveGraph( Graph, OverwriteCache ) {
		UIInvalidatingCache( Graph['Query'], OverwriteCache, function (data) {
			if( 'error' in data ) {
				UIError( data['error'] );
			} else {
				if( data['invalidatingcache'] ) {
					if( UIConfirm( 'The changes that have been made involve the data cache invalidation.\n' +
						'In order to keep cached data it is suggested to create a new graph with current settings.\n\n' +
						'By saving this graph cached data will be lost.\n\n' +
						'Proceed anyway?' ) ) {
						UISaveGraph( Graph, true );
					}
				} else {
					$.ajax( {
						url: $SCRIPT_ROOT + '/saveGraph',
						type: 'POST',
						contentType: 'application/json',
						data: JSON.stringify( {
							'Graph': Graph
						} ),
					} ).done( function( data ) {
						if( 'error' in data ) {
							UIError( data['error'] );
						} else {
							$('#editor').hide();
							UILoadGraphs();
							$('[name=loadgraph]').val( data['ID'] );
							UIEvent_LoadGraphChange();
							UISuccess();
						}
					} ).error( function( jqXHR, textStatus, errorThrown ) {
						UIError( UIAjaxError( 'Error saving the graph', jqXHR, textStatus, errorThrown ) );
					} );
				}
			}
		} );
	}

	function UIEvent_SaveGraphClick() {
		var Graph = UIGetGraph();
		if( !Graph ) {
			return;
		}

		UISaveGraph( Graph, false );
	}

	function UIGetSelectedAggr() {
		var SelVal = $('[name=aggr]').val();
		for( FieldIdx in GlobalConfig['NFDUMP_FIELDS'] ) {
			if( GlobalConfig['NFDUMP_FIELDS'][FieldIdx]['ID'] == SelVal ) {
				return GlobalConfig['NFDUMP_FIELDS'][FieldIdx];
			}
		}
		return null;
	}

	function UIAggrRequiresArg() {
		var SelAggr = UIGetSelectedAggr();
		if( SelAggr ) {
			return SelAggr['ArgRequired'];
		} else {
			return false;
		}
	}

	function UIGetSelectedGraph() {
		GraphID = $('[name=loadgraph]').val();
		Graph = null;
		for( GraphIdx in Graphs ) {
			if( Graphs[GraphIdx]['ID'] == GraphID ) {
				Graph = Graphs[GraphIdx];
			}
		}
		return Graph;
	}

	function UILoadSelectedGraph() {
		Graph = UIGetSelectedGraph();
		UILoadGraph( Graph )
	}

	function UIEvent_NewGraphClick() {
		UILoadGraph( null );
		return;
	}

	function UILoadGraph( Graph ) {
		$('[name=graphid]').val( Graph ? Graph['ID'] : '' );

		$('[name=title]').val( Graph ? Graph['Title'] : '' );

		$('[name=sources] option').each( function() {
			if( Graph ) {
				if( Graph['Query']['SourceFiles']['SourceIDs'].indexOf( $(this).val() ) >= 0 ) {
					$(this).prop( 'selected', true );
				} else {
					$(this).prop( 'selected', false );
				}
			} else {
				$(this).prop( 'selected', false );
			}
		} );

		$('[name=filter]').val( Graph ? Graph['Query']['Filter'] : '' );
		$('[name=aggr]').val( Graph ? Graph['Query']['AggrField'] : '' );
		$('[name=arg]').val( Graph ? Graph['Query']['AggrFieldArg'] : '' );
		$('[name=top]').val( Graph ? Graph['Query']['TopN'] : '' );
		$('[name=orderby]').val( Graph ? Graph['Query']['OrderBy']['ColName'] : 'bytes' );
		$('[name=orderby_dir]').val( Graph ? Graph['Query']['OrderBy']['Order'] : 'DESC' );

		$('[name=draw_what]').val( Graph ? ( 'Draw' in Graph ? Graph['Draw']['What'] : 'bytes' ) : 'bytes' );
		$('[name=draw_how]').val( Graph ? ( 'Draw' in Graph ? Graph['Draw']['How'] : 'bar' ) : 'bar' );

		$('[name=basedir]').val( Graph ? Graph['Query']['SourceFiles']['BaseDir'] : '' );
		$('[name=filenameformat]').val( Graph ? Graph['Query']['SourceFiles']['FileNameFormat'] : '' );
		$('[name=interval]').val( Graph ? Graph['Query']['SourceFiles']['Interval'] : '' );
		$('[name=cachefilename]').val( Graph ? Graph['Query']['CacheFile'] : '' );

		$('#schedules').empty();
		$('[name=enable_scheduling]').removeAttr('checked');

		if( Graph ) {
			if( 'Scheduler' in Graph ) {
				if( 'Schedules' in Graph['Scheduler'] ) {
					if( Graph['Scheduler']['Schedules'].length > 0 ) {
						Graph['Scheduler']['Schedules'].forEach( function(Schedule) {
							UIAddSchedule( Schedule );
						} );
						$('[name=enable_scheduling]').prop('checked',true);
					}
				}
				if( 'MaxCache' in Graph['Scheduler'] ) {
					$('[name=scheduler_maxcache]').val( Graph['Scheduler']['MaxCache'] );
				}
			}
		}
	}

	function UIEvent_DeleteGraphClick() {
		Graph = UIGetSelectedGraph();

		if( confirm('Really delete graph with title ' + Graph['Title'] + '?') ) {
			$.ajax( {
				url: $SCRIPT_ROOT + '/deleteGraph',
				dataType: 'json',
				data: { 'GraphID': Graph['ID'] }
			} ).done( function( data ) {
				if( 'error' in data ) {
					UIError( data['error'] );
				} else {
					UILoadGraphs();
					UIEvent_LoadGraphChange();
					UISuccess();
				}
			} ).error( function( jqXHR, textStatus, errorThrown ) {
				UIError( UIAjaxError( 'Error deleting graph', jqXHR, textStatus, errorThrown ) );
			} );
		}
	}

	function UIEvent_CloneGraphClick() {
		$('[name=graphid]').val( '' );
		$('[name=title]').val( 'Copy of ' + $('[name=title]').val() );
		$('[name=loadgraph]').val( '' );
		$('[name=cachefilename]').val( '' );
		UIEnableDisableGUI();
	}

	function UILoadGraphs() {
		$('[name=loadgraph] > option:not(:first)').filter(':not(:last)').remove();

		$.ajax( {
			url: $SCRIPT_ROOT + '/getGraphs',
			async: false,
			dataType: 'json'
		} ).done( function( data ) {
			Graphs = data;

			Options = [];

			for( GraphIdx in Graphs ) {
				Graph = Graphs[ GraphIdx ];
				Options.push( { val: Graph['ID'], text: Graph['Title'] } );
			}

			Options.sort( function(a,b) {
				if( a['text'] > b['text'] ) {
					return 1;
				} else {
					return 0;
				}
			} );

			for( OptionIdx in Options ) {
				$('[name=loadgraph] > option:last').before( new Option( Options[ OptionIdx ]['text'], Options[ OptionIdx ]['val'] ) );
			}
		} ).error( function( jqXHR, textStatus, errorThrown ) {
			UIError( UIAjaxError( 'Error loading graphs', jqXHR, textStatus, errorThrown ) );
		} );
	}

	function UIEnableDisableElements( UIElements, Enabled ) {
		if( Enabled ) {
			UIElements.forEach( function(e) {
				$(e).removeAttr('disabled');
			} );
		} else {
			UIElements.forEach( function(e) {
				$(e).prop('disabled',true);
			} );
		}
	}

	function UIEnableDisableGUI() {
		UIElements = [ '#edit', '#delete', '#draw', '[name=start]', '[name=stop]' ];

		var ValidGraphSelected = false;
		if( $('[name=loadgraph]').val() != null ) {
			if( $('[name=loadgraph]').val() != '' ) {
				ValidGraphSelected = true;
			}
		}

		UIEnableDisableElements( UIElements, ValidGraphSelected );
	}

	function UIEvent_LoadGraphChange() {
		if( $('[name=loadgraph]').val() != null ) {
			if( $('[name=loadgraph]').val() != '' ) {
				UILoadSelectedGraph();
			} else {
				UIEvent_NewGraphClick();
				$('#editor').show();
			}
		}
		UIEnableDisableGUI();
		UIEvent_EnableSchedulingClick();
	}

	function UIInvalidatingCache( Query, OverwriteCache, callbackDone ) {
		if( OverwriteCache ) {
			callbackDone( { 'invalidatingcache': false } );
		} else {
			$.ajax( {
				url: $SCRIPT_ROOT + '/invalidatingCache',
				type: 'POST',
				contentType: 'application/json',
				dataType: 'json',
				data: JSON.stringify( {
					'Query': Query
				} )

			} ).done( function( data ) {
				callbackDone( data );

			} ).error( function( jqXHR, textStatus, errorThrown ) {
				callbackDone( { 'error': UIAjaxError( 'Error checking cached data', jqXHR, textStatus, errorThrown ) } );
			} );
		}
	}

	function UIDrawGraph( Graph, OverwriteCache, callbackComplete ) {
		UIInvalidatingCache( Graph['Query'], OverwriteCache, function (data) {
			if( 'error' in data ) {
				UIError( data['error'] );
				callbackComplete();
			} else {
				if( data['invalidatingcache'] ) {
					if( UIConfirm( 'The changes that have been made involve the data cache invalidation.\n' +
							'It is suggested to create a new graph with current settings.\n\n' +
							'By drawing this graph cached data will be lost.\n\n' +
							'Proceed anyway?' ) ) {
						UIDrawGraph( Graph, true, callbackComplete ) 
					} else {
						callbackComplete();
					}
				} else {
					$('#pngtosave').hide();
					$('#saveaspng').hide();
					$('#myChart').html( '<div style="width: 100%; height: auto; text-align: center; vertical-align: middle;">Loading data...</div>' );

					setTimeout( function() {
						$.ajax( {
							url: $SCRIPT_ROOT + '/getData',
							type: 'POST',
							contentType: 'application/json',
							dataType: 'json',
							data: JSON.stringify( {
								'Graph': Graph
							} )
						} ).done( function( data ) {
							if( 'error' in data ) {
								UIError( data['error'] );
							} else {
								drawChart( data );
							}
						} ).error( function( jqXHR, textStatus, errorThrown ) {
							UIError( UIAjaxError( 'Error loading data', jqXHR, textStatus, errorThrown ) );
						} ).complete( function() {
							callbackComplete();
						} );
					}, 100 );
				}
			}
		} );
	}

	function UIEvent_DrawGraphClick() {
		Graph = UIGetGraph();

		if( !Graph ) {
			UIEvent_EditClick();
			return;
		}

		if( $('[name=start]').val().trim() == '' ) {
			UIError('Missing start date/time');
			return;
		}
		if( $('[name=stop]').val().trim() == '' ) {
			UIError('Missing stop date/time');
			return;
		}

		var StartStopValid = true;

		[ 'Start', 'Stop' ].forEach( function(e) {
			try {
				DT = new moment( $('[name=' + e.toLowerCase() + ']').val().trim(), 'YYYY-MM-DD HH:mm' );
				if( !DT.isValid() ) {
					UIError('Invalid ' + e + ' date/time');
					StartStopValid = false;
					return false;
				} else {
					UISavePreference( 'Last' + e, $('[name=' + e.toLowerCase() + ']').val().trim() );
				}
				Graph[e] = DT.unix();
			} catch(e) {
				UIError('Invalid ' + e + ' date/time');
				return false;
			}
		} )

		if( !StartStopValid ) {
			return;
		}

		if( Graph['Stop'] <= Graph['Start'] ) {
			UIError('Stop must be later than start');
			return;
		}

		if( Graph['Stop'] - Graph['Start'] > 12*60*60 ) {
			if( !UIConfirm('An interval bigger than 12 hours has been selected.\nThis may require a long processing time if netflow data has not previously cached.\n\nProceed anyway?') ) {
				return;
			}
		}

		UIElements = [ '#new', '#edit', '#delete', '#draw', '[name=start]', '[name=stop]' ];
		UIEnableDisableElements( UIElements, false );

		// litte timeout to allow the browser to refresh elements' disabled state
		setTimeout( function() {
			UIDrawGraph( Graph, false, function() {
				UIEnableDisableElements( UIElements, true );
			} );
		}, 100 );
	}

	function UIEvent_EditClick() {
		$('#editor').show();
		UIEnableDisableGUI();
	}

	function UISavePreference( PrefName, PrefVal ) {
		try {
			if( 'localStorage' in window && window['localStorage'] !== null ) {
				localStorage.setItem( PrefName, PrefVal );
			}
		} catch (e) {
			return;
		}
	}

	function UIEvent_TabClick( li ) {
		var SelectedTabID = null;

		var a = $(li).children('a');

		if( $(a).attr('href') ) {
			SelectedTabID = $(a).attr('href');
			$(li).data( 'href', SelectedTabID );
			$(a).removeAttr('href');
			$(a).addClass('disabled-tab');
			$(li).addClass('selected');
		} else {
			return;
		}

		$('#tabs .tabs-nav li').each( function() {
			if( !( $(this).is( $(li) ) ) ) {
				var a = $(this).children('a');
				if( !$(a).attr('href') ) {
					$(a).attr( 'href', $(this).data( 'href' ) );
					$(a).removeClass('disabled-tab');
					$(this).removeClass('selected');
				}
			}
		} );

		$('.tab').each( function() {
			if( $(this).is( $(SelectedTabID) ) ) {
				$(this).show();
			} else {
				$(this).hide();
			}
		} );
	}

	function UIGetSchedule( callbackOnError ) {
		var Schedule = {};

		var BreakException= {};
		try {
			[ 'Date', 'Time' ].forEach( function(DateTime) {
				[ 'Start', 'Stop' ].forEach( function(StartStop) {
					UseElement = '[name=use_scheduler_' + StartStop.toLowerCase() + DateTime.toLowerCase() + ']';
					ValElement = '[name=scheduler_' + StartStop.toLowerCase() + DateTime.toLowerCase() + ']';
					DTFormat = DateTime == 'Date' ? 'YYYY-MM-DD' : 'HH:mm';

					if( $(UseElement).is(':checked') ) {
						var DT = new moment( $(ValElement).val().trim(), DTFormat );
						if( !DT.isValid() ) {
							callbackOnError('Invalid ' + StartStop.toLowerCase() + ' ' + DateTime.toLowerCase() + ' for the new schedule');
							throw BreakException;
						} else {
							Schedule[StartStop + DateTime] = DT.format( DTFormat );
						}
					}
				} );
			} );
		} catch(exception) {
			if (exception!==BreakException) {
				throw exception;
			} else {
				return;
			}
		}

		if( ( 'StartDate' in Schedule ) && ( 'StopDate' in Schedule ) ) {
			if( moment( Schedule['StopDate'], 'YYYY-MM-DD' ) <= moment( Schedule['StartDate'], 'YYYY-MM-DD' ) ) {
				callbackOnError('The new schedule\' stop date must be later than the start date');
				return;
			}
		}

		if( $('[name=use_scheduler_dow]').is(':checked') ) {
			Schedule['DoW'] = [];
			Schedule['DoW'] = $('[name=scheduler_dow]:checked').map( function() { return parseInt( $(this).val() ); } ).get();
			if( Schedule['DoW'].length == 0 ) {
				callbackOnError('One or more days of week must be selected');
				return;
			}
		}

		return Schedule;
	}

	function UIUpdateNewScheduleDescription() {
		var Schedule = UIGetSchedule( function(err) {
			$('#new_schedule_description').text( 'Error: ' + err );
		} );
		if( Schedule ) {
			Description = UIGetScheduleDescription( Schedule );
			$('#new_schedule_description').text( Description );
		}
	}

	function UIResetSchedule() {
		[ 'Date', 'Time' ].forEach( function(DateTime) {
			[ 'Start', 'Stop' ].forEach( function(StartStop) {
				UseElement = '[name=use_scheduler_' + StartStop.toLowerCase() + DateTime.toLowerCase() + ']';
				ValElement = '[name=scheduler_' + StartStop.toLowerCase() + DateTime.toLowerCase() + ']';
				$(UseElement).removeAttr('checked');
				$(ValElement).val('');
			} );
		} );

		$('.use_schedule_param').removeAttr('checked');
		$('[name=scheduler_dow]').removeAttr('checked');
		$('[name=scheduler_maxcache]').val('');
	}

	function UIGetScheduleDescription( Schedule ) {
		var Description = '';

		if( 'StartDate' in Schedule ) {
			Description += Description == '' ? '' : ', ';
			Description += 'beginning on ' + moment( Schedule['StartDate'] ).format( 'ddd ll' );
		}
		if( 'StopDate' in Schedule ) {
			Description += Description == '' ? '' : ', ';
			Description += 'until ' + moment( Schedule['StopDate'] ).format( 'ddd ll' );
		}
		if( ( 'StartTime' in Schedule ) && ( 'StopTime' in Schedule ) ) {
			Description += Description == '' ? '' : ', ';
			Description += 'between ' + Schedule['StartTime'] + ' and ' + Schedule['StopTime'];
		} else {
			if( 'StartTime' in Schedule ) {
				Description += Description == '' ? '' : ', ';
				Description += 'between ' + Schedule['StartTime'] + ' and 23:59';
			}
			if( 'StopTime' in Schedule ) {
				Description += Description == '' ? '' : ', ';
				Description += 'between 0:00 and ' + Schedule['StopTime'];
			}
		}
		if( 'DoW' in Schedule ) {
			if( Schedule['DoW'].length > 0 ) {
				Description += Description == '' ? '' : ', ';

				var Days = '';
				for( wd in Schedule['DoW'] ) {
					if( Days != '' ) {
						Days += ', ';
					}
					Days += moment().isoWeekday( Schedule['DoW'][wd] ).format('ddd');
				};
				Description += 'only on ' + Days;
			}
		}

		if( Description == '' ) {
			Description = 'Always';
		}

		return Description;
	}

	function UIAddSchedule( Schedule ) {
		var newSchedule = $('#template_new_schedule').clone(true).removeAttr('id').appendTo( $('#schedules') );
		$(newSchedule).find('span').text( UIGetScheduleDescription( Schedule ) );
		$(newSchedule).show();
		$(newSchedule).data( 'Schedule', Schedule );
		$('#schedules').show();
	}

	function UIEvent_AddScheduleClick() {
		var Schedule = UIGetSchedule( UIError );
		if( Schedule ) {
			UIAddSchedule( Schedule );
			UIResetSchedule();
			UIEvent_EnableSchedulingClick();
		}	
	}

	function UIEvent_RemoveSchedule(obj) {
		$(obj).closest('div').remove();
		if( $('#schedules div').length == 0 ) {
			$('#schedules').hide();
		}
	}

	function UIEvent_EnableSchedulingClick() {
		var SchedulerEnabled = $('[name=enable_scheduling]').is(':checked');

		if( SchedulerEnabled ) {
			$('.new_schedule_param').each( function() {
				var Enabled = $('[name=use_' + $(this).attr('name') + ']').is(':checked');
				if( Enabled ) {
					$(this).removeAttr('disabled');
				} else {
					$(this).prop('disabled',true);
				}
			} );

			UIUpdateNewScheduleDescription();
			$('#schedules').show();
			$('#new_schedule').show();
		} else {
			$('#schedules').hide();
			$('#new_schedule').hide();
		}
	}

	function UILoadPreferences() {
		try {
			if( 'localStorage' in window && window['localStorage'] !== null ) {
				var LastStart = localStorage.getItem('LastStart');
				var LastStop = localStorage.getItem('LastStop');
				$('[name=start').val( LastStart );
				$('[name=stop').val( LastStop );
			}
		} catch (e) {
			return;
		}
	}

	function UISetup() {

		$.ajax( {
			url: $SCRIPT_ROOT + '/getConfig',
			dataType: 'json'
		} ).done( function( data ) {
			GlobalConfig = data;

			for( SourceIdx in GlobalConfig['NETFLOW_SOURCESID'] ) {
				$('[name=sources]').append( new Option( GlobalConfig['NETFLOW_SOURCESID'][SourceIdx], GlobalConfig['NETFLOW_SOURCESID'][SourceIdx] ) );
			}

			for( FieldIdx in GlobalConfig['NFDUMP_FIELDS'] ) {
				Field = GlobalConfig['NFDUMP_FIELDS'][FieldIdx];
				$('[name=aggr]').append( new Option( Field['Name'], Field['ID'] ) );
			}

			$('[name=aggr]').change( function() {
				if( UIAggrRequiresArg() ) {
					$('.argdiv').show();
				} else {
					$('.argdiv').hide();
				}
			} );

			$('[name=loadgraph]').change( function() {
				UIEvent_LoadGraphChange();
			} );

			$('#delete').click( function() {
				UIEvent_DeleteGraphClick();
			} );

			$('#edit').click( function() {
				UIEvent_EditClick();
			} );

			$('#closeeditor').click( function() {
				$('#editor').hide();
				UIEnableDisableGUI();
			} );

			$('#clone').click( function() {
				UIEvent_CloneGraphClick();
			} );

			$('#new').click( function() {
				$('[name=loadgraph]').val( '' );
				UIEvent_LoadGraphChange();
			} );

			$('#save').click( function() {
				UIEvent_SaveGraphClick();
			} );

			$('#draw').click( function() {
				UIEvent_DrawGraphClick();
			} );

			if( $('[name=start]').prop( 'type' ) !== 'datetime' ) {
				$('.datetime').datetimepicker( {
					format: 'Y-m-d H:i',
					formatDate: 'Y/m/d',
					formatTime: 'H:i',
					dayOfWeekStart: moment().startOf('isoweek').weekday(),
					datepicker: true,
					timepicker: true,
					mask: true,
					step: 10,
					maxDate: new Date()
				} );
			}

			if( $('.date').prop( 'type' ) !== 'date' ) {
				$('.date').datetimepicker( {
					format: 'Y-m-d',
					formatDate: 'Y/m/d',
					dayOfWeekStart: moment().startOf('isoweek').weekday(),
					datepicker: true,
					timepicker: false,
					mask: true
				} );
			}

			if( $('.time').prop( 'type' ) !== 'time' ) {
				$('.time').datetimepicker( {
					format: 'H:i',
					formatTime: 'H:i',
					datepicker: false,
					timepicker: true,
					step: 30,
					mask: true
				} );
			}

			$('#tabs .tabs-nav li').click( function() {
				UIEvent_TabClick( $(this) );
			} );
			UIEvent_TabClick( $('#tabs .tabs-nav li:first') );

			$('[name=enable_scheduling]').click( function() {
				UIEvent_EnableSchedulingClick();
			} );

			$('.use_schedule_param').click( function() {
				UIEvent_EnableSchedulingClick();
			} ).change( function() {
				UIUpdateNewScheduleDescription();
			} );

			$('.new_schedule_param').change( function() {
				UIUpdateNewScheduleDescription();
			} );

			$('#addschedule').click( function() {
				UIEvent_AddScheduleClick();
			} );

			$('#template_new_schedule a').click( function(e) {
				e.preventDefault();
				UIEvent_RemoveSchedule( $(this) );
			} );

			$('#pngtosave a').click( function(e) {
				e.preventDefault();
				$('#pngtosave').hide();
			} );

			$('#filters_info').attr( 'title', 'The syntax used for filter is the same used by nfdump.\nSee the FILTER section of man nfdump for details.\nUse @include %filters%/filename to include files from the var directory.');

			UIEnableDisableGUI();
			UILoadPreferences();
			UILoadGraphs();

			if( $CHECKUPDATES_ENABLE ) {
				setTimeout( function() {
					CheckNewRelease( {
						current_release: $CURRENT_RELEASE,
						owner: 'pierky',
						repo: 'flowgraph',
						include_pre_releases: $CHECKUPDATES_PRERELEASE,
						check_interval: $CHECKUPDATES_INTERVAL,

						done: function( Results ) {
							if( Results['new_release_found'] ) {
								var NewReleaseTitle = '';
								NewReleaseTitle += Results['new_release']['version'];
								if( Results['new_release']['name'] != '' ) {
									NewReleaseTitle += ' - ' + Results['new_release']['name'];
								}
								NewReleaseTitle += '\n';
								NewReleaseTitle += Results['new_release']['published_at'];

								if( Results['new_release']['prerelease'] ) {
									NewReleaseTitle += '\n';
									NewReleaseTitle += 'pre-release';
								}
								
								$('#newrelease').attr( 'href', Results['new_release']['url'] );
								$('#newrelease').attr( 'title', NewReleaseTitle );
								$('#newrelease').show();
							}
						},

						error: function( ErrMsg ) {
							console.log( 'Error while checking for updates: ' + ErrMsg );
						}
					} );
				}, 1000 );
			}
		} ).error( function( jqXHR, textStatus, errorThrown ) {
                        UIError( UIAjaxError( 'Error loading global configuration', jqXHR, textStatus, errorThrown ) );
		} );
	}

	$(document).ready( function() { 
		UISetup();
	} )

